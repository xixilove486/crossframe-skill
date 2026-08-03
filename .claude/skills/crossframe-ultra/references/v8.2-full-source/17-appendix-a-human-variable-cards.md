# CrossFrame Ultra v8.2 附录A　人类变量接口卡册

Raw SHA256: `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
Source role: `division`
Paragraph range: `V82-P2906`-`V82-P4477`
Paragraph count: `1572`
Tables: `V82-T064, V82-T065, V82-T066, V82-T067, V82-T068, V82-T069, V82-T070, V82-T071, V82-T072, V82-T073, V82-T074, V82-T075, V82-T076, V82-T077, V82-T078, V82-T079, V82-T080, V82-T081, V82-T082, V82-T083, V82-T084, V82-T085, V82-T086, V82-T087, V82-T088, V82-T089, V82-T090, V82-T091, V82-T092, V82-T093, V82-T094, V82-T095, V82-T096, V82-T097, V82-T098, V82-T099, V82-T100, V82-T101, V82-T102, V82-T103, V82-T104, V82-T105, V82-T106, V82-T107, V82-T108, V82-T109, V82-T110, V82-T111, V82-T112, V82-T113, V82-T114, V82-T115, V82-T116, V82-T117, V82-T118, V82-T119`

## Source Paragraphs

<!-- source-paragraph:V82-P2906 style=PartTitle -->
附录A　人类变量接口卡册

<!-- source-paragraph:V82-P2907 style=BodyCJK -->
本附录完整收录第七部分十一项人类变量(HV01-HV11)的接口卡。每张卡按 A-E 五区登记:A 身份、命题与适用范围;B 正式依赖与推论边界;C 九轴尺度与对象合同;D 状态、证据与变量流;E 承接、责任、规范、上限与纠错。卡片内容与 v8.0 逐字一致,仅调整了表格版式与单元格内分行。

<!-- source-paragraph:V82-P2908 style=BodyCJK -->
以下 11 张卡片逐项展开每个变量的全部 39 个正式字段，并与合同 JSON 逐值同步。依赖项的空集合明确写作“无（空集合）”；它只表示该类依赖没有登记对象，不表示证据充分或经验成立。条件支持路由必须逐条整体读取，不能把不同路由的有利条件事后并取。

<!-- source-paragraph:V82-P2909 style=SecH2 -->
A.1　HV01 结构域（完整接口卡）

<!-- source-paragraph:V82-P2910 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P2911 style=TableHead -->
字段

<!-- source-paragraph:V82-P2912 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P2913 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P2914 style=TableText -->
HV01

<!-- source-paragraph:V82-P2915 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P2916 style=TableText -->
human_variable:HV01

<!-- source-paragraph:V82-P2917 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P2918 style=TableText -->
结构域

<!-- source-paragraph:V82-P2919 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P2920 style=TableText -->
H

<!-- source-paragraph:V82-P2921 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P2922 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P2923 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P2924 style=TableText -->
D0只声明候选人类对象；只有预注册G1-instance显示候选分组相对匹配N0在预选结果上取得超过阈值的样本外或外推增益时，才在该实例范围登记有限有效结构域。

<!-- source-paragraph:V82-P2925 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P2926 style=TableText -->
关系、团队、组织、制度与公共议题

<!-- source-paragraph:V82-P2927 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P2928 style=TableText -->
对象、边界、尺度、时间窗、同一性或零模型不完整

<!-- source-paragraph:V82-P2929 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P2930 style=TableHead -->
字段

<!-- source-paragraph:V82-P2931 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P2932 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P2933 style=TableText -->
1. D0

<!-- source-paragraph:V82-P2934 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P2935 style=TableText -->
1. E1

<!-- source-paragraph:V82-P2936 style=TableText -->
2. EVIDENCE

<!-- source-paragraph:V82-P2937 style=TableText -->
3. SOURCE

<!-- source-paragraph:V82-P2938 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P2939 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P2940 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P2941 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P2942 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P2943 style=TableText -->
1. route_id=HV01-R0-candidate-object；

<!-- source-paragraph:V82-P2944 style=TableText -->
claim_level=candidate_description；

<!-- source-paragraph:V82-P2945 style=TableText -->
when=D0对象合同完整，但尚无符合资格且result_state=supported的G1-instance。；

<!-- source-paragraph:V82-P2946 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P2947 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P2948 style=TableText -->
allowed_conclusion=登记候选人类对象、材料集合、边界争议与G1补证需求。；

<!-- source-paragraph:V82-P2949 style=TableText -->
result_ceiling=仅到候选对象描述；不得称有限有效结构域，也不得限定HV02-HV11的经验对象范围。

<!-- source-paragraph:V82-P2950 style=TableText -->
2. route_id=HV01-R1-effective-domain；

<!-- source-paragraph:V82-P2951 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P2952 style=TableText -->
when=同一对象、尺度、窗口、K与外推单元内的预注册G1-instance取得supported。；

<!-- source-paragraph:V82-P2953 style=TableText -->
additional_inferential_requires=G1-instance；

<!-- source-paragraph:V82-P2954 style=TableText -->
additional_protocol_requires=E4；

<!-- source-paragraph:V82-P2955 style=TableText -->
allowed_conclusion=登记该实例范围内的有限有效结构域、对象识别强度、边界可信度和适用窗。；

<!-- source-paragraph:V82-P2956 style=TableText -->
result_ceiling=只限预注册SP/T/K与generalization_unit；不得作终极本体、统一意志或授权判断。

<!-- source-paragraph:V82-P2957 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P2958 style=TableText -->
1. 只在G1-instance预注册对象、尺度、窗口、结果与外推单位内登记有限有效结构域及识别强度

<!-- source-paragraph:V82-P2959 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P2960 style=TableText -->
1. 命名即客观共同体2. 共同处境即共同意愿

<!-- source-paragraph:V82-P2961 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P2962 style=TableHead -->
字段

<!-- source-paragraph:V82-P2963 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P2964 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P2965 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：关系或事件单元、候选成员总体、边界内外分布及分组规则；X=空间范围：共同场所、组织边界、数字平台与跨域外部环境；T=时间跨度：识别窗口、成员变动周期与边界历史；O=组织层级：角色、团队、组织、制度至治理生态；C=因果层次：原始事件、互动机制、中观关系结构、制度与系统条件；R=观察分辨率：原始互动、事件序列、成员个案、边界分布、指标与摘要，并登记压缩损失；I=影响范围：直接成员、被排除者、间接受影响者、二阶外溢、跨域与代际位置；N=网络拓扑范围：成员关系、边界连接、孤立点与跨域桥接；J=管辖与授权范围：对象命名、边界采用及后续处置分别登记授权；不适用轴须登记not_applicable理由

<!-- source-paragraph:V82-P2966 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P2967 style=TableText -->
由D0声明的候选对象；只有通过预注册G1-instance相对匹配N0的阈值检验后，才在该实例范围登记为有限有效结构域

<!-- source-paragraph:V82-P2968 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P2969 style=TableText -->
1. 对象合同2. 参与与受影响位置

<!-- source-paragraph:V82-P2970 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P2971 style=TableText -->
1. 单位与总体

<!-- source-paragraph:V82-P2972 style=TableText -->
2. 代表性

<!-- source-paragraph:V82-P2973 style=TableText -->
3. J轴

<!-- source-paragraph:V82-P2974 style=TableText -->
4. 低可见位置

<!-- source-paragraph:V82-P2975 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P2976 style=TableText -->
1. 有效成员、关系和同一性可随尺度改变

<!-- source-paragraph:V82-P2977 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P2978 style=TableText -->
1. 无意向、制度或责任接口的非人系统

<!-- source-paragraph:V82-P2979 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P2980 style=TableText -->
1. 局部群体直接代表全部受影响者

<!-- source-paragraph:V82-P2981 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P2982 style=TableHead -->
字段

<!-- source-paragraph:V82-P2983 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P2984 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P2985 style=TableText -->
1. 候选2. 可识别3. 边界争议4. 不成立

<!-- source-paragraph:V82-P2986 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P2987 style=TableText -->
1. 边界内外关系密度与约束差异

<!-- source-paragraph:V82-P2988 style=TableText -->
2. 成员进入、退出与被排除记录

<!-- source-paragraph:V82-P2989 style=TableText -->
3. 共同问题、资源通道或制度规则的重复共现

<!-- source-paragraph:V82-P2990 style=TableText -->
4. 改变分组规则后对象识别是否稳定

<!-- source-paragraph:V82-P2991 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P2992 style=TableText -->
1. D0候选对象与同一性记录

<!-- source-paragraph:V82-P2993 style=TableText -->
2. G1-instance预注册表及匹配N0

<!-- source-paragraph:V82-P2994 style=TableText -->
3. 训练与样本外或外推结果

<!-- source-paragraph:V82-P2995 style=TableText -->
4. 候选分组与竞争分组的增益比较

<!-- source-paragraph:V82-P2996 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P2997 style=TableText -->
1. D0只提供候选对象字段，不构成结构成立证据

<!-- source-paragraph:V82-P2998 style=TableText -->
2. 预注册G1-instance及匹配N0、阈值、模型类、样本或外推单位

<!-- source-paragraph:V82-P2999 style=TableText -->
3. 观察位置、竞争分组与E1协议

<!-- source-paragraph:V82-P3000 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3001 style=TableText -->
1. 仅在G1-instance通过后限定其余十变量的对象范围；未通过时保持候选或材料集合

<!-- source-paragraph:V82-P3002 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3003 style=TableText -->
登记识别窗口、边界变动与成员变化时滞

<!-- source-paragraph:V82-P3004 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3005 style=TableText -->
记录边界争议、成员缺席和观察覆盖

<!-- source-paragraph:V82-P3006 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3007 style=TableText -->
无法安全表达或未被采样的位置不得被总体代表

<!-- source-paragraph:V82-P3008 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3009 style=TableText -->
1. 成员2. 被排除者3. 边界外成本承担者

<!-- source-paragraph:V82-P3010 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3011 style=TableHead -->
字段

<!-- source-paragraph:V82-P3012 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3013 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3014 style=TableText -->
1. 关系网络2. 组织边界3. 制度记录

<!-- source-paragraph:V82-P3015 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3016 style=TableText -->
1. 提出结构域判断的分析者

<!-- source-paragraph:V82-P3017 style=TableText -->
2. 使用该判断的决策者

<!-- source-paragraph:V82-P3018 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3019 style=TableText -->
描述性H-World接口，不产生正当性

<!-- source-paragraph:V82-P3020 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3021 style=TableText -->
只有G1-instance通过时，且仅限预注册对象、尺度、窗口、结果与外推单位，才可登记解释级有限有效对象；否则仅为候选对象或材料集合

<!-- source-paragraph:V82-P3022 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3023 style=TableText -->
本变量只生成候选结构域、边界争议与补证需求描述，不授权纳入、排除或处置；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3024 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3025 style=TableText -->
1. 同一场所中反复共现的人群没有稳定关系或共同约束

<!-- source-paragraph:V82-P3026 style=TableText -->
2. 分析者划定的群组在改变分组规则后立即消失

<!-- source-paragraph:V82-P3027 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3028 style=TableText -->
依appeal_and_rollback_rule，成员与受影响位置可经安全可达、反报复通道挑战边界、代表性和同一性判据，并触发与原命名或决策链独立的复核

<!-- source-paragraph:V82-P3029 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3030 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销结构域登记、移除其对下游对象范围的效力并恢复为材料集合，保留版本与完成验证

<!-- source-paragraph:V82-P3031 style=SecH2 -->
A.2　HV02 边界与接口（完整接口卡）

<!-- source-paragraph:V82-P3032 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3033 style=TableHead -->
字段

<!-- source-paragraph:V82-P3034 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3035 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3036 style=TableText -->
HV02

<!-- source-paragraph:V82-P3037 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3038 style=TableText -->
human_variable:HV02

<!-- source-paragraph:V82-P3039 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3040 style=TableText -->
边界与接口

<!-- source-paragraph:V82-P3041 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3042 style=TableText -->
H

<!-- source-paragraph:V82-P3043 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3044 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3045 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3046 style=TableText -->
人类边界必须同时登记成员、资源、信息、权利、责任与跨界接口。

<!-- source-paragraph:V82-P3047 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3048 style=TableText -->
存在纳入、排除、交换或管辖的人类结构

<!-- source-paragraph:V82-P3049 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3050 style=TableText -->
正式边界与实际边界混同或排除项不可见

<!-- source-paragraph:V82-P3051 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3052 style=TableHead -->
字段

<!-- source-paragraph:V82-P3053 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3054 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3055 style=TableText -->
1. human_variable:HV01

<!-- source-paragraph:V82-P3056 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3057 style=TableText -->
1. E1

<!-- source-paragraph:V82-P3058 style=TableText -->
2. EVIDENCE

<!-- source-paragraph:V82-P3059 style=TableText -->
3. SOURCE

<!-- source-paragraph:V82-P3060 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3061 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3062 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3063 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3064 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3065 style=TableText -->
1. route_id=HV02-R0-boundary-inventory；

<!-- source-paragraph:V82-P3066 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3067 style=TableText -->
when=成员、资源、信息、权利、责任、跨界接口及正式—实际边界差异可逐项登记。；

<!-- source-paragraph:V82-P3068 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3069 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3070 style=TableText -->
allowed_conclusion=描述边界状态、接口通达性、守门位置、拒绝记录与排除风险。；

<!-- source-paragraph:V82-P3071 style=TableText -->
result_ceiling=只到边界与接口清单；不得断言边界已产生因果选择效应。

<!-- source-paragraph:V82-P3072 style=TableText -->
2. route_id=HV02-R1-selective-effect；

<!-- source-paragraph:V82-P3073 style=TableText -->
claim_level=conditional_effect；

<!-- source-paragraph:V82-P3074 style=TableText -->
when=预注册边界或接口变动经符合资格的G2-instance显示对指定跨界流、准入或拒绝结果有超过阈值的通道效应。；

<!-- source-paragraph:V82-P3075 style=TableText -->
additional_inferential_requires=G2-instance；

<!-- source-paragraph:V82-P3076 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3077 style=TableText -->
allowed_conclusion=登记指定通道、窗口与位置上的边界选择效应及跨界成本分布。；

<!-- source-paragraph:V82-P3078 style=TableText -->
result_ceiling=只限已检验通道与结果；不得从空间、组织或影响范围推出J轴管辖与处置权。

<!-- source-paragraph:V82-P3079 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3080 style=TableText -->
1. 边界选择性2. 接口通达性3. 跨界成本

<!-- source-paragraph:V82-P3081 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3082 style=TableText -->
1. 边界等于封闭

<!-- source-paragraph:V82-P3083 style=TableText -->
2. 成员身份等于同意

<!-- source-paragraph:V82-P3084 style=TableText -->
3. 影响范围等于管辖权

<!-- source-paragraph:V82-P3085 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3086 style=TableHead -->
字段

<!-- source-paragraph:V82-P3087 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3088 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3089 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次跨界事件、接口使用个案、成员类别总体、准入拒绝分布及聚合规则；X=空间范围：物理入口、组织边界、数字接口、司法辖区与跨域通道；T=时间跨度：边界生效期、接口等待、迁移时滞与重组周期；O=组织层级：使用者角色、守门团队、组织、制度至治理生态；C=因果层次：跨界事件、守门互动机制、接口结构、制度规则与系统条件；R=观察分辨率：原始准入拒绝记录、使用序列、个案、流量分布、服务指标与摘要，并登记压缩损失；I=影响范围：直接使用者、被排除者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：接口节点、守门瓶颈、替代路径与跨域连接；J=管辖与授权范围：纳入、排除、接口改变及权利责任调整分别登记授权；升格须记录逐轴差值

<!-- source-paragraph:V82-P3090 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3091 style=TableText -->
对资源、信息、权利或责任流产生选择性的边界

<!-- source-paragraph:V82-P3092 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3093 style=TableText -->
1. 内外位置2. 跨界通道3. 权利责任边界

<!-- source-paragraph:V82-P3094 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3095 style=TableText -->
1. 新成员类别

<!-- source-paragraph:V82-P3096 style=TableText -->
2. 跨域接口

<!-- source-paragraph:V82-P3097 style=TableText -->
3. 代表与授权

<!-- source-paragraph:V82-P3098 style=TableText -->
4. 保护继承

<!-- source-paragraph:V82-P3099 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3100 style=TableText -->
1. 成员、接口与实际控制边界可改变

<!-- source-paragraph:V82-P3101 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3102 style=TableText -->
1. 无成员、权利或责任概念的非人边界

<!-- source-paragraph:V82-P3103 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3104 style=TableText -->
1. 空间或组织范围扩大自动产生管辖权

<!-- source-paragraph:V82-P3105 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3106 style=TableHead -->
字段

<!-- source-paragraph:V82-P3107 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3108 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3109 style=TableText -->
1. 开放

<!-- source-paragraph:V82-P3110 style=TableText -->
2. 选择性开放

<!-- source-paragraph:V82-P3111 style=TableText -->
3. 封闭

<!-- source-paragraph:V82-P3112 style=TableText -->
4. 争议

<!-- source-paragraph:V82-P3113 style=TableText -->
5. 重组

<!-- source-paragraph:V82-P3114 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3115 style=TableText -->
1. 成员资格、准入与退出决定

<!-- source-paragraph:V82-P3116 style=TableText -->
2. 资源、信息、权利和责任的跨界流量

<!-- source-paragraph:V82-P3117 style=TableText -->
3. 守门节点、等待时间与拒绝理由

<!-- source-paragraph:V82-P3118 style=TableText -->
4. 正式边界与实际通行边界的差异

<!-- source-paragraph:V82-P3119 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3120 style=TableText -->
1. 成员名单与例外

<!-- source-paragraph:V82-P3121 style=TableText -->
2. 接口使用记录

<!-- source-paragraph:V82-P3122 style=TableText -->
3. 跨界流和拒绝记录

<!-- source-paragraph:V82-P3123 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3124 style=TableText -->
1. HV01结构域2. 角色与授权

<!-- source-paragraph:V82-P3125 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3126 style=TableText -->
1. HV05承接

<!-- source-paragraph:V82-P3127 style=TableText -->
2. HV07写回

<!-- source-paragraph:V82-P3128 style=TableText -->
3. PF-9退出

<!-- source-paragraph:V82-P3129 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3130 style=TableText -->
记录边界生效、变更、退出和申诉时滞

<!-- source-paragraph:V82-P3131 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3132 style=TableText -->
记录非正式边界、代理访问和数字空间漂移

<!-- source-paragraph:V82-P3133 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3134 style=TableText -->
无法接入接口、无法退出或受保护不公开的位置

<!-- source-paragraph:V82-P3135 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3136 style=TableText -->
1. 成员

<!-- source-paragraph:V82-P3137 style=TableText -->
2. 申请者

<!-- source-paragraph:V82-P3138 style=TableText -->
3. 被排除者

<!-- source-paragraph:V82-P3139 style=TableText -->
4. 边界外承担者

<!-- source-paragraph:V82-P3140 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3141 style=TableHead -->
字段

<!-- source-paragraph:V82-P3142 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3143 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3144 style=TableText -->
1. 成员规则

<!-- source-paragraph:V82-P3145 style=TableText -->
2. 访问机制

<!-- source-paragraph:V82-P3146 style=TableText -->
3. 法律或制度边界

<!-- source-paragraph:V82-P3147 style=TableText -->
4. 技术接口

<!-- source-paragraph:V82-P3148 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3149 style=TableText -->
1. 边界制定者2. 接口运营者3. 授权者

<!-- source-paragraph:V82-P3150 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3151 style=TableText -->
边界事实与边界正当性分离

<!-- source-paragraph:V82-P3152 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3153 style=TableText -->
接口与影响证据充分时至诊断级

<!-- source-paragraph:V82-P3154 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3155 style=TableText -->
本变量只生成边界状态、接口障碍、排除风险与测试需求描述，不授权改变准入、退出、权利或资源流；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3156 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3157 style=TableText -->
1. 正式成员边界与实际资源控制边界相反

<!-- source-paragraph:V82-P3158 style=TableText -->
2. 数字接口开放但物理、语言或安全门槛使部分位置无法进入

<!-- source-paragraph:V82-P3159 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3160 style=TableText -->
依appeal_and_rollback_rule，边界内外受影响者可经安全可达、反报复通道挑战纳入、排除和接口障碍，并触发与原边界决策链独立的复核

<!-- source-paragraph:V82-P3161 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3162 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正成员与拒绝记录、实际恢复受影响的准入权利或接口状态并撤销错误边界行动，保留版本与完成验证

<!-- source-paragraph:V82-P3163 style=SecH2 -->
A.3　HV03 指向锚点（完整接口卡）

<!-- source-paragraph:V82-P3164 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3165 style=TableHead -->
字段

<!-- source-paragraph:V82-P3166 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3167 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3168 style=TableText -->
HV03

<!-- source-paragraph:V82-P3169 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3170 style=TableText -->
human_variable:HV03

<!-- source-paragraph:V82-P3171 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3172 style=TableText -->
指向锚点

<!-- source-paragraph:V82-P3173 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3174 style=TableText -->
H

<!-- source-paragraph:V82-P3175 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3176 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3177 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3178 style=TableText -->
目标、身份、记忆、承诺、恐惧或共同问题只有改变资源与行动时才构成指向锚点。

<!-- source-paragraph:V82-P3179 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3180 style=TableText -->
具有意向、协调或共同问题的人类结构

<!-- source-paragraph:V82-P3181 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3182 style=TableText -->
只有口号、解释者投射或被强制的一致表达

<!-- source-paragraph:V82-P3183 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3184 style=TableHead -->
字段

<!-- source-paragraph:V82-P3185 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3186 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3187 style=TableText -->
1. human_variable:HV01

<!-- source-paragraph:V82-P3188 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3189 style=TableText -->
1. E2

<!-- source-paragraph:V82-P3190 style=TableText -->
2. EVIDENCE

<!-- source-paragraph:V82-P3191 style=TableText -->
3. SOURCE

<!-- source-paragraph:V82-P3192 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3193 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3194 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3195 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3196 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3197 style=TableText -->
1. route_id=HV03-R0-candidate-anchor；

<!-- source-paragraph:V82-P3198 style=TableText -->
claim_level=candidate_description；

<!-- source-paragraph:V82-P3199 style=TableText -->
when=目标、身份、记忆、承诺、恐惧或共同问题有可追踪表达与承载形式，但尚无符合资格的H1-instance。；

<!-- source-paragraph:V82-P3200 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3201 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3202 style=TableText -->
allowed_conclusion=登记候选意义材料、异质表达、代表性争议与H1补证需求。；

<!-- source-paragraph:V82-P3203 style=TableText -->
result_ceiling=仅称候选意义表达；不得称有效指向锚点或共同意志。

<!-- source-paragraph:V82-P3204 style=TableText -->
2. route_id=HV03-R1-effective-anchor；

<!-- source-paragraph:V82-P3205 style=TableText -->
claim_level=conditional_effect；

<!-- source-paragraph:V82-P3206 style=TableText -->
when=预注册H1-instance在资源配置、行动选择或协调结果中唯一预选的判据取得supported。；

<!-- source-paragraph:V82-P3207 style=TableText -->
additional_inferential_requires=H1-instance；

<!-- source-paragraph:V82-P3208 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3209 style=TableText -->
allowed_conclusion=登记该实例、结果家族、尺度与窗口内的条件性有效指向锚点。；

<!-- source-paragraph:V82-P3210 style=TableText -->
result_ceiling=不外推到未选资源、行动或协调结果，也不推出真实同意、统一内心或强制统一意义。

<!-- source-paragraph:V82-P3211 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3212 style=TableText -->
1. 条件性的协调方向与冲突锚点

<!-- source-paragraph:V82-P3213 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3214 style=TableText -->
1. 群体具有统一内心

<!-- source-paragraph:V82-P3215 style=TableText -->
2. 共同语言等于真实同意

<!-- source-paragraph:V82-P3216 style=TableText -->
3. 目标正当

<!-- source-paragraph:V82-P3217 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3218 style=TableHead -->
字段

<!-- source-paragraph:V82-P3219 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3220 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3221 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次表达或行动、主体个案、候选参与总体、立场分布及聚合规则；X=空间范围：关系现场、组织空间、数字公共空间与跨域传播范围；T=时间跨度：表达—行动窗口、承诺周期、漂移与解耦时滞；O=组织层级：行动角色、团队、组织、制度至公共治理生态；C=因果层次：表达事件、意义—行动互动机制、中观协调结构、制度安排与系统条件；R=观察分辨率：原始表达与行动、事件序列、个案、立场分布、协调指标与摘要，并登记压缩损失；I=影响范围：直接参与者、异议者、间接受影响者、二阶协调后果、跨域与代际影响；N=网络拓扑范围：表达传播、协调连接、异质簇群与桥接节点；J=管辖与授权范围：锚点命名、代表性采用、协调或统一要求分别登记授权；必须保留异质锚点

<!-- source-paragraph:V82-P3222 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3223 style=TableText -->
能改变资源或行动的目标、身份、记忆、承诺、恐惧或共同问题

<!-- source-paragraph:V82-P3224 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3225 style=TableText -->
1. 意义到资源或行动的桥接

<!-- source-paragraph:V82-P3226 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3227 style=TableText -->
1. 代表规则

<!-- source-paragraph:V82-P3228 style=TableText -->
2. 异质性

<!-- source-paragraph:V82-P3229 style=TableText -->
3. 成本收益分布

<!-- source-paragraph:V82-P3230 style=TableText -->
4. J轴

<!-- source-paragraph:V82-P3231 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3232 style=TableText -->
1. 锚点内容、强度和承载主体可改变

<!-- source-paragraph:V82-P3233 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3234 style=TableText -->
1. 无意向、意义或承诺能力的非人系统

<!-- source-paragraph:V82-P3235 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3236 style=TableText -->
1. 局部表达直接升级为共同意志

<!-- source-paragraph:V82-P3237 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3238 style=TableHead -->
字段

<!-- source-paragraph:V82-P3239 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3240 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3241 style=TableText -->
1. 分散

<!-- source-paragraph:V82-P3242 style=TableText -->
2. 凝聚

<!-- source-paragraph:V82-P3243 style=TableText -->
3. 竞争

<!-- source-paragraph:V82-P3244 style=TableText -->
4. 固化

<!-- source-paragraph:V82-P3245 style=TableText -->
5. 解耦

<!-- source-paragraph:V82-P3246 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3247 style=TableText -->
1. 预注册意义表达出现前后的资源配置差异

<!-- source-paragraph:V82-P3248 style=TableText -->
2. 行动选择、协作完成率或冲突模式变化

<!-- source-paragraph:V82-P3249 style=TableText -->
3. 不同位置对锚点的接受、拒绝与替代表述

<!-- source-paragraph:V82-P3250 style=TableText -->
4. 比较条件下结果差异是否超过预定阈值

<!-- source-paragraph:V82-P3251 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3252 style=TableText -->
1. 资源调整

<!-- source-paragraph:V82-P3253 style=TableText -->
2. 行动序列

<!-- source-paragraph:V82-P3254 style=TableText -->
3. 承诺与退出记录

<!-- source-paragraph:V82-P3255 style=TableText -->
4. 冲突证据

<!-- source-paragraph:V82-P3256 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3257 style=TableText -->
1. 参与位置2. 表达安全3. 资源与行动数据

<!-- source-paragraph:V82-P3258 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3259 style=TableText -->
1. 生成事件2. 承接动员3. 规范选择议程

<!-- source-paragraph:V82-P3260 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3261 style=TableText -->
区分短期口号、长期承诺与代际记忆

<!-- source-paragraph:V82-P3262 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3263 style=TableText -->
记录沉默、强制一致与内部异质性

<!-- source-paragraph:V82-P3264 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3265 style=TableText -->
低安全位置的不同目标不得被聚合抹去

<!-- source-paragraph:V82-P3266 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3267 style=TableText -->
1. 认同者

<!-- source-paragraph:V82-P3268 style=TableText -->
2. 异议者

<!-- source-paragraph:V82-P3269 style=TableText -->
3. 被代表者

<!-- source-paragraph:V82-P3270 style=TableText -->
4. 成本承担者

<!-- source-paragraph:V82-P3271 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3272 style=TableHead -->
字段

<!-- source-paragraph:V82-P3273 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3274 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3275 style=TableText -->
1. 叙事

<!-- source-paragraph:V82-P3276 style=TableText -->
2. 承诺

<!-- source-paragraph:V82-P3277 style=TableText -->
3. 共同记忆

<!-- source-paragraph:V82-P3278 style=TableText -->
4. 制度目标

<!-- source-paragraph:V82-P3279 style=TableText -->
5. 问题定义

<!-- source-paragraph:V82-P3280 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3281 style=TableText -->
1. 提出代表性主张者2. 据此配置资源者

<!-- source-paragraph:V82-P3282 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3283 style=TableText -->
锚点存在不证明其正当

<!-- source-paragraph:V82-P3284 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3285 style=TableText -->
有行动桥接时至解释级，无桥接时仅描述表达

<!-- source-paragraph:V82-P3286 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3287 style=TableText -->
本变量只生成候选锚点、异质表达、比较结果与补证需求描述，不授权统一意义、代表意愿或协调行动；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3288 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3289 style=TableText -->
1. 反复出现的口号没有改变任何资源配置或行动

<!-- source-paragraph:V82-P3290 style=TableText -->
2. 高压场景中的一致表达掩盖相互冲突的真实目标

<!-- source-paragraph:V82-P3291 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3292 style=TableText -->
依appeal_and_rollback_rule，成员可经安全可达、反报复通道否认代表性、提交异质目标或拒绝被锚定，并触发与原锚点判断链独立的复核

<!-- source-paragraph:V82-P3293 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3294 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销锚点命名、移除其代表性与下游协调效力并恢复异质表达状态，保留版本与完成验证

<!-- source-paragraph:V82-P3295 style=SecH2 -->
A.4　HV04 生成节点（完整接口卡）

<!-- source-paragraph:V82-P3296 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3297 style=TableHead -->
字段

<!-- source-paragraph:V82-P3298 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3299 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3300 style=TableText -->
HV04

<!-- source-paragraph:V82-P3301 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3302 style=TableText -->
human_variable:HV04

<!-- source-paragraph:V82-P3303 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3304 style=TableText -->
生成节点

<!-- source-paragraph:V82-P3305 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3306 style=TableText -->
H

<!-- source-paragraph:V82-P3307 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3308 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3309 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3310 style=TableText -->
生成必须分流为生成条件GC、生成主体GS与生成事件GE，允许无可识别主体的涌现型生成。

<!-- source-paragraph:V82-P3311 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3312 style=TableText -->
人类结构中新行动、组织、制度或状态转移的形成

<!-- source-paragraph:V82-P3313 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3314 style=TableText -->
条件被人格化、事件被当作主体或主体资格不明

<!-- source-paragraph:V82-P3315 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3316 style=TableHead -->
字段

<!-- source-paragraph:V82-P3317 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3318 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3319 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3320 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3321 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P3322 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3323 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3324 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3325 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3326 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3327 style=TableText -->
1. route_id=HV04-R0-generation-typing；

<!-- source-paragraph:V82-P3328 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3329 style=TableText -->
when=GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；

<!-- source-paragraph:V82-P3330 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3331 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3332 style=TableText -->
allowed_conclusion=分别登记候选生成条件、候选生成主体与候选生成事件，不将三者互相替代。；

<!-- source-paragraph:V82-P3333 style=TableText -->
result_ceiling=只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。

<!-- source-paragraph:V82-P3334 style=TableText -->
2. route_id=HV04-R1-generation-mechanism；

<!-- source-paragraph:V82-P3335 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P3336 style=TableText -->
when=预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；

<!-- source-paragraph:V82-P3337 style=TableText -->
additional_inferential_requires=G2-instance；

<!-- source-paragraph:V82-P3338 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3339 style=TableText -->
allowed_conclusion=登记指定尺度、窗口和通道内的候选生成机制及其GC、GS、GE分型。；

<!-- source-paragraph:V82-P3340 style=TableText -->
result_ceiling=不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。

<!-- source-paragraph:V82-P3341 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3342 style=TableText -->
1. 条件性生成路径2. 有主体或无主体生成

<!-- source-paragraph:V82-P3343 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3344 style=TableText -->
1. 技术或危机具有意图

<!-- source-paragraph:V82-P3345 style=TableText -->
2. 生成主体自动拥有持续授权

<!-- source-paragraph:V82-P3346 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3347 style=TableHead -->
字段

<!-- source-paragraph:V82-P3348 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3349 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3350 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：条件暴露、主体行动与生成事件单元，各自个案总体、分布及聚合规则；X=空间范围：生成现场、组织或平台边界、扩散区域与跨域环境；T=时间跨度：条件积累期、主体行动窗、事件时点与扩散时滞；O=组织层级：行动角色、生成团队、组织、制度至治理生态；C=因果层次：生成事件、主体—条件互动机制、中观生成结构、制度安排与系统条件；R=观察分辨率：原始条件行动事件、生成序列、个案、结果分布、转移指标与摘要，并登记压缩损失；I=影响范围：直接生成参与者、承接者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：条件传播、主体协作、事件扩散与涌现连接；J=管辖与授权范围：生成识别、启动改变、资源投入及扩散处置分别登记授权；GC、GS、GE分别登记尺度

<!-- source-paragraph:V82-P3351 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3352 style=TableText -->
形成可检测状态转移的条件、主体与事件组合

<!-- source-paragraph:V82-P3353 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3354 style=TableText -->
1. GC、GS、GE强类型分离

<!-- source-paragraph:V82-P3355 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3356 style=TableText -->
1. 新单位与总体

<!-- source-paragraph:V82-P3357 style=TableText -->
2. 代表关系

<!-- source-paragraph:V82-P3358 style=TableText -->
3. 责任类型

<!-- source-paragraph:V82-P3359 style=TableText -->
4. 外部影响

<!-- source-paragraph:V82-P3360 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3361 style=TableText -->
1. 生成主体、条件与事件可随尺度改变

<!-- source-paragraph:V82-P3362 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3363 style=TableText -->
1. 没有新状态形成或生成主张的稳定描述

<!-- source-paragraph:V82-P3364 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3365 style=TableText -->
1. 把条件或事件升格为有意图主体

<!-- source-paragraph:V82-P3366 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3367 style=TableHead -->
字段

<!-- source-paragraph:V82-P3368 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3369 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3370 style=TableText -->
1. 潜在

<!-- source-paragraph:V82-P3371 style=TableText -->
2. 触发

<!-- source-paragraph:V82-P3372 style=TableText -->
3. 形成

<!-- source-paragraph:V82-P3373 style=TableText -->
4. 中断

<!-- source-paragraph:V82-P3374 style=TableText -->
5. 扩散

<!-- source-paragraph:V82-P3375 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3376 style=TableText -->
1. 候选条件出现、改变或移除的时间记录

<!-- source-paragraph:V82-P3377 style=TableText -->
2. 生成主体的能力、授权、决策与实际行动

<!-- source-paragraph:V82-P3378 style=TableText -->
3. 生成事件前后预注册状态转移

<!-- source-paragraph:V82-P3379 style=TableText -->
4. 无主体涌现时局部互动与总体结果的桥接记录

<!-- source-paragraph:V82-P3380 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3381 style=TableText -->
1. 启动记录

<!-- source-paragraph:V82-P3382 style=TableText -->
2. 条件窗口

<!-- source-paragraph:V82-P3383 style=TableText -->
3. 主体行动

<!-- source-paragraph:V82-P3384 style=TableText -->
4. 无主体互动机制

<!-- source-paragraph:V82-P3385 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3386 style=TableText -->
1. 指向锚点2. 资源与制度条件3. 因果合同

<!-- source-paragraph:V82-P3387 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3388 style=TableText -->
1. 承接需求2. 状态转移3. 责任链起点

<!-- source-paragraph:V82-P3389 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3390 style=TableText -->
登记条件积累、触发事件与形成时滞

<!-- source-paragraph:V82-P3391 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3392 style=TableText -->
记录共同生成、无主体涌现和不可识别主体

<!-- source-paragraph:V82-P3393 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3394 style=TableText -->
被遗漏的非正式启动者与受影响位置

<!-- source-paragraph:V82-P3395 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3396 style=TableText -->
1. 启动者

<!-- source-paragraph:V82-P3397 style=TableText -->
2. 承接者

<!-- source-paragraph:V82-P3398 style=TableText -->
3. 受益者

<!-- source-paragraph:V82-P3399 style=TableText -->
4. 受影响者

<!-- source-paragraph:V82-P3400 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3401 style=TableHead -->
字段

<!-- source-paragraph:V82-P3402 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3403 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3404 style=TableText -->
1. 启动者

<!-- source-paragraph:V82-P3405 style=TableText -->
2. 程序

<!-- source-paragraph:V82-P3406 style=TableText -->
3. 技术设施

<!-- source-paragraph:V82-P3407 style=TableText -->
4. 关系网络

<!-- source-paragraph:V82-P3408 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3409 style=TableText -->
1. 实际行动者2. 决策者3. 授权者

<!-- source-paragraph:V82-P3410 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3411 style=TableText -->
生成事实不证明正当或责任完整

<!-- source-paragraph:V82-P3412 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3413 style=TableText -->
机制链完整时至解释级

<!-- source-paragraph:V82-P3414 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3415 style=TableText -->
本变量只生成GC、GS、GE候选分型、状态转移描述与补证需求，不授权启动、扩散或停止生成过程；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3416 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3417 style=TableText -->
1. 技术条件被错误描述成具有目标的生成主体

<!-- source-paragraph:V82-P3418 style=TableText -->
2. 无统一发起者的涌现过程被强行归因给一个可见人物

<!-- source-paragraph:V82-P3419 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3420 style=TableText -->
依appeal_and_rollback_rule，被归为生成主体者可经安全可达、反报复通道挑战意图、角色与授权归因，并触发与原分型或决策链独立的复核

<!-- source-paragraph:V82-P3421 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3422 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正GC、GS、GE类型，实际移除错误意图或责任归因及其下游效力，保留版本与完成验证

<!-- source-paragraph:V82-P3423 style=SecH2 -->
A.5　HV05 行动承接层（完整接口卡）

<!-- source-paragraph:V82-P3424 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3425 style=TableHead -->
字段

<!-- source-paragraph:V82-P3426 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3427 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3428 style=TableText -->
HV05

<!-- source-paragraph:V82-P3429 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3430 style=TableText -->
human_variable:HV05

<!-- source-paragraph:V82-P3431 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3432 style=TableText -->
行动承接层

<!-- source-paragraph:V82-P3433 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3434 style=TableText -->
H

<!-- source-paragraph:V82-P3435 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3436 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3437 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3438 style=TableText -->
执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。

<!-- source-paragraph:V82-P3439 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3440 style=TableText -->
需要持续行动、维护、照护或执行的人类结构

<!-- source-paragraph:V82-P3441 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3442 style=TableText -->
低权限执行者被默认归为主要责任人或承接能力被当作义务

<!-- source-paragraph:V82-P3443 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3444 style=TableHead -->
字段

<!-- source-paragraph:V82-P3445 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3446 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3447 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3448 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3449 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P3450 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3451 style=TableText -->
1. H2

<!-- source-paragraph:V82-P3452 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3453 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3454 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3455 style=TableText -->
1. route_id=HV05-R0-carrier-responsibility-split；

<!-- source-paragraph:V82-P3456 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3457 style=TableText -->
when=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；

<!-- source-paragraph:V82-P3458 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3459 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3460 style=TableText -->
allowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；

<!-- source-paragraph:V82-P3461 style=TableText -->
result_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。

<!-- source-paragraph:V82-P3462 style=TableText -->
2. route_id=HV05-R1-functional-carrier-effect；

<!-- source-paragraph:V82-P3463 style=TableText -->
claim_level=conditional_effect；

<!-- source-paragraph:V82-P3464 style=TableText -->
when=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；

<!-- source-paragraph:V82-P3465 style=TableText -->
additional_inferential_requires=G2-instance；

<!-- source-paragraph:V82-P3466 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3467 style=TableText -->
allowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；

<!-- source-paragraph:V82-P3468 style=TableText -->
result_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。

<!-- source-paragraph:V82-P3469 style=TableText -->
3. route_id=HV05-R2-intertemporal-reproduction；

<!-- source-paragraph:V82-P3470 style=TableText -->
claim_level=intertemporal_explanation；

<!-- source-paragraph:V82-P3471 style=TableText -->
when=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；

<!-- source-paragraph:V82-P3472 style=TableText -->
additional_inferential_requires=G2-instance、G3-instance；

<!-- source-paragraph:V82-P3473 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3474 style=TableText -->
allowed_conclusion=登记指定窗口与载体内的跨期承接或再生产候选。；

<!-- source-paragraph:V82-P3475 style=TableText -->
result_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。

<!-- source-paragraph:V82-P3476 style=TableText -->
4. route_id=HV05-R3-historical-carrier-trace；

<!-- source-paragraph:V82-P3477 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3478 style=TableText -->
when=H5-instance对唯一预选的具体载体与持久判据取得supported。；

<!-- source-paragraph:V82-P3479 style=TableText -->
additional_inferential_requires=H5-instance；

<!-- source-paragraph:V82-P3480 style=TableText -->
additional_protocol_requires=E4；

<!-- source-paragraph:V82-P3481 style=TableText -->
allowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；

<!-- source-paragraph:V82-P3482 style=TableText -->
result_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。

<!-- source-paragraph:V82-P3483 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3484 style=TableText -->
1. 承接缺口2. 任务资源错配3. 责任分流

<!-- source-paragraph:V82-P3485 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3486 style=TableText -->
1. 最可见者等于主要责任人

<!-- source-paragraph:V82-P3487 style=TableText -->
2. 能承担所以应承担

<!-- source-paragraph:V82-P3488 style=TableText -->
3. 非人载体承担责任

<!-- source-paragraph:V82-P3489 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3490 style=TableHead -->
字段

<!-- source-paragraph:V82-P3491 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3492 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3493 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度

<!-- source-paragraph:V82-P3494 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3495 style=TableText -->
实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度

<!-- source-paragraph:V82-P3496 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3497 style=TableText -->
1. CV不等于RS

<!-- source-paragraph:V82-P3498 style=TableText -->
2. 成本与受益分别登记

<!-- source-paragraph:V82-P3499 style=TableText -->
3. 停止权

<!-- source-paragraph:V82-P3500 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3501 style=TableText -->
1. 任务聚合

<!-- source-paragraph:V82-P3502 style=TableText -->
2. 代表和委托

<!-- source-paragraph:V82-P3503 style=TableText -->
3. 六类责任

<!-- source-paragraph:V82-P3504 style=TableText -->
4. 外部成本

<!-- source-paragraph:V82-P3505 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3506 style=TableText -->
1. 承接载体和责任主体可随层级改变

<!-- source-paragraph:V82-P3507 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3508 style=TableText -->
1. 无主体行动、责任或维护要求的非人过程

<!-- source-paragraph:V82-P3509 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3510 style=TableText -->
1. 个体承接直接等于组织责任

<!-- source-paragraph:V82-P3511 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3512 style=TableHead -->
字段

<!-- source-paragraph:V82-P3513 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3514 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3515 style=TableText -->
1. 充足

<!-- source-paragraph:V82-P3516 style=TableText -->
2. 脆弱

<!-- source-paragraph:V82-P3517 style=TableText -->
3. 过载

<!-- source-paragraph:V82-P3518 style=TableText -->
4. 断裂

<!-- source-paragraph:V82-P3519 style=TableText -->
5. 替代

<!-- source-paragraph:V82-P3520 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3521 style=TableText -->
1. 任务实际执行、维护、记录与修复日志

<!-- source-paragraph:V82-P3522 style=TableText -->
2. 资源、容量、时间和成本流向

<!-- source-paragraph:V82-P3523 style=TableText -->
3. 停止权、替代安排与承接转移记录

<!-- source-paragraph:V82-P3524 style=TableText -->
4. 决策、授权、监督、受益与补救依据

<!-- source-paragraph:V82-P3525 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3526 style=TableText -->
1. 任务流

<!-- source-paragraph:V82-P3527 style=TableText -->
2. 工时与资源

<!-- source-paragraph:V82-P3528 style=TableText -->
3. 维护记录

<!-- source-paragraph:V82-P3529 style=TableText -->
4. 停止和拒绝记录

<!-- source-paragraph:V82-P3530 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3531 style=TableText -->
1. 生成需求2. 资源3. 授权4. 角色

<!-- source-paragraph:V82-P3532 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3533 style=TableText -->
1. 实现状态转移2. 成本分布3. 结构负荷

<!-- source-paragraph:V82-P3534 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3535 style=TableText -->
登记排班、维护周期、积压与恢复时滞

<!-- source-paragraph:V82-P3536 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3537 style=TableText -->
记录隐性劳动、非正式照护和边界外成本

<!-- source-paragraph:V82-P3538 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3539 style=TableText -->
低权限、非正式与不可退出承接者

<!-- source-paragraph:V82-P3540 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3541 style=TableText -->
1. 承接者

<!-- source-paragraph:V82-P3542 style=TableText -->
2. 受益者

<!-- source-paragraph:V82-P3543 style=TableText -->
3. 被服务者

<!-- source-paragraph:V82-P3544 style=TableText -->
4. 替代者

<!-- source-paragraph:V82-P3545 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3546 style=TableHead -->
字段

<!-- source-paragraph:V82-P3547 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3548 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3549 style=TableText -->
1. 人员

<!-- source-paragraph:V82-P3550 style=TableText -->
2. 岗位

<!-- source-paragraph:V82-P3551 style=TableText -->
3. 程序

<!-- source-paragraph:V82-P3552 style=TableText -->
4. 设施

<!-- source-paragraph:V82-P3553 style=TableText -->
5. 制度

<!-- source-paragraph:V82-P3554 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3555 style=TableText -->
1. 行为责任者

<!-- source-paragraph:V82-P3556 style=TableText -->
2. 决策责任者

<!-- source-paragraph:V82-P3557 style=TableText -->
3. 授权责任者

<!-- source-paragraph:V82-P3558 style=TableText -->
4. 监督责任者

<!-- source-paragraph:V82-P3559 style=TableText -->
5. 受益责任者

<!-- source-paragraph:V82-P3560 style=TableText -->
6. 补救责任者

<!-- source-paragraph:V82-P3561 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3562 style=TableText -->
承接事实不产生继续承担义务

<!-- source-paragraph:V82-P3563 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3564 style=TableText -->
资源与责任链完整时至诊断级

<!-- source-paragraph:V82-P3565 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3566 style=TableText -->
本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3567 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3568 style=TableText -->
1. 最可见的低权限执行者不是决策、授权或受益责任主体

<!-- source-paragraph:V82-P3569 style=TableText -->
2. 自动化设施承担传导任务但不能承担道德或法律责任

<!-- source-paragraph:V82-P3570 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3571 style=TableText -->
依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核

<!-- source-paragraph:V82-P3572 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3573 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证

<!-- source-paragraph:V82-P3574 style=SecH2 -->
A.6　HV06 动力—承接链（完整接口卡）

<!-- source-paragraph:V82-P3575 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3576 style=TableHead -->
字段

<!-- source-paragraph:V82-P3577 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3578 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3579 style=TableText -->
HV06

<!-- source-paragraph:V82-P3580 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3581 style=TableText -->
human_variable:HV06

<!-- source-paragraph:V82-P3582 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3583 style=TableText -->
动力—承接链

<!-- source-paragraph:V82-P3584 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3585 style=TableText -->
H

<!-- source-paragraph:V82-P3586 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3587 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3588 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3589 style=TableText -->
从指向、生成到执行、维护与偿付的链条必须逐段登记通道、资源、成本、责任和时滞。

<!-- source-paragraph:V82-P3590 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3591 style=TableText -->
人类集体行动、项目、组织与制度运行

<!-- source-paragraph:V82-P3592 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3593 style=TableText -->
用热情、愿景或命令替代承接与偿付证据

<!-- source-paragraph:V82-P3594 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3595 style=TableHead -->
字段

<!-- source-paragraph:V82-P3596 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3597 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3598 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3599 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3600 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P3601 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3602 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3603 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3604 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3605 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3606 style=TableText -->
1. route_id=HV06-R0-segment-map；

<!-- source-paragraph:V82-P3607 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3608 style=TableText -->
when=至少一个链段的输入、输出、时延、损耗、中断、资源、成本与边界可观察。；

<!-- source-paragraph:V82-P3609 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3610 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3611 style=TableText -->
allowed_conclusion=登记局部链段、缺失桥、时滞、损耗、中断点与成本位置。；

<!-- source-paragraph:V82-P3612 style=TableText -->
result_ceiling=不得由单一链段或动力语言宣称完整链条或有效通道。

<!-- source-paragraph:V82-P3613 style=TableText -->
2. route_id=HV06-R1-complete-chain-composition；

<!-- source-paragraph:V82-P3614 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3615 style=TableText -->
when=指向、生成与承接三个接口记录可在同一对象、尺度、窗口与量的映射中逐段连接。；

<!-- source-paragraph:V82-P3616 style=TableText -->
additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05；

<!-- source-paragraph:V82-P3617 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3618 style=TableText -->
allowed_conclusion=登记完整候选动力—承接链及逐段证据覆盖。；

<!-- source-paragraph:V82-P3619 style=TableText -->
result_ceiling=只到候选链条组成；接口记录齐全不等于各链段具有因果效力。

<!-- source-paragraph:V82-P3620 style=TableText -->
3. route_id=HV06-R2-effective-channel；

<!-- source-paragraph:V82-P3621 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P3622 style=TableText -->
when=完整候选链已组成，且符合资格的G2-instance逐段识别指定通道对目标转移的效应。；

<!-- source-paragraph:V82-P3623 style=TableText -->
additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05、G2-instance；

<!-- source-paragraph:V82-P3624 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3625 style=TableText -->
allowed_conclusion=登记已检验链段和窗口内的有效动力—承接通道、损耗与中断机制。；

<!-- source-paragraph:V82-P3626 style=TableText -->
result_ceiling=不得从一次贯通推出跨期再生产、责任、正当性或行动授权。

<!-- source-paragraph:V82-P3627 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3628 style=TableText -->
1. 链条瓶颈2. 动力与承接脱节3. 隐性偿付

<!-- source-paragraph:V82-P3629 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3630 style=TableText -->
1. 动力强等于可持续

<!-- source-paragraph:V82-P3631 style=TableText -->
2. 失败归因意愿不足

<!-- source-paragraph:V82-P3632 style=TableText -->
3. 承接者应自行补洞

<!-- source-paragraph:V82-P3633 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3634 style=TableHead -->
字段

<!-- source-paragraph:V82-P3635 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3636 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3637 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单个链节事件、链条个案、同类链总体、输入输出分布及聚合规则；X=空间范围：行动现场、项目或组织边界、数字协作空间与跨域外溢；T=时间跨度：启动、维持、中断、恢复窗口及跨期周期；O=组织层级：发起角色、执行团队、组织、制度至治理生态；C=因果层次：链节事件、动力—资源—任务互动机制、中观承接链、制度安排与系统条件；R=观察分辨率：原始任务资源记录、链节序列、链条个案、损耗分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接发起与承接位置、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖链、替代路径、瓶颈、反馈连接与跨域桥接；J=管辖与授权范围：目标采用、任务分配、资源投入、停止与试验分别登记授权；逐段标明跨轴位置

<!-- source-paragraph:V82-P3638 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3639 style=TableText -->
把指向和生成转为持续行动的可追踪链条

<!-- source-paragraph:V82-P3640 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3641 style=TableText -->
1. 指向、生成、承接、资源、成本和责任链

<!-- source-paragraph:V82-P3642 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3643 style=TableText -->
1. 跨层桥接

<!-- source-paragraph:V82-P3644 style=TableText -->
2. 聚合损失

<!-- source-paragraph:V82-P3645 style=TableText -->
3. 责任继承

<!-- source-paragraph:V82-P3646 style=TableText -->
4. 保护底板

<!-- source-paragraph:V82-P3647 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3648 style=TableText -->
1. 节点、通道和瓶颈可随组织尺度改变

<!-- source-paragraph:V82-P3649 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3650 style=TableText -->
1. 无意向动力与人类承接的非人过程

<!-- source-paragraph:V82-P3651 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3652 style=TableText -->
1. 局部动力或单一节点直接代表完整链条

<!-- source-paragraph:V82-P3653 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3654 style=TableHead -->
字段

<!-- source-paragraph:V82-P3655 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3656 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3657 style=TableText -->
1. 贯通

<!-- source-paragraph:V82-P3658 style=TableText -->
2. 迟滞

<!-- source-paragraph:V82-P3659 style=TableText -->
3. 过载

<!-- source-paragraph:V82-P3660 style=TableText -->
4. 断裂

<!-- source-paragraph:V82-P3661 style=TableText -->
5. 替代

<!-- source-paragraph:V82-P3662 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3663 style=TableText -->
1. 锚点转化为任务、预算、规则或排程的记录

<!-- source-paragraph:V82-P3664 style=TableText -->
2. 每段输入输出、时延、损耗与中断点

<!-- source-paragraph:V82-P3665 style=TableText -->
3. 承接者容量、停止与替代路径变化

<!-- source-paragraph:V82-P3666 style=TableText -->
4. 链条输出对目标结果的实际贡献

<!-- source-paragraph:V82-P3667 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3668 style=TableText -->
1. 资源流

<!-- source-paragraph:V82-P3669 style=TableText -->
2. 任务与维护记录

<!-- source-paragraph:V82-P3670 style=TableText -->
3. 偿付与成本

<!-- source-paragraph:V82-P3671 style=TableText -->
4. 时滞

<!-- source-paragraph:V82-P3672 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3673 style=TableText -->
1. 指向锚点2. 生成节点3. 承接层

<!-- source-paragraph:V82-P3674 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3675 style=TableText -->
1. 行动结果2. 负荷3. 反馈与演化痕迹

<!-- source-paragraph:V82-P3676 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3677 style=TableText -->
逐段登记启动、传导、维护和偿付时滞

<!-- source-paragraph:V82-P3678 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3679 style=TableText -->
记录断点、替代通道与边界外偿付

<!-- source-paragraph:V82-P3680 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3681 style=TableText -->
非正式、低可见和跨组织承接位置

<!-- source-paragraph:V82-P3682 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3683 style=TableText -->
1. 发起者

<!-- source-paragraph:V82-P3684 style=TableText -->
2. 承接者

<!-- source-paragraph:V82-P3685 style=TableText -->
3. 受益者

<!-- source-paragraph:V82-P3686 style=TableText -->
4. 成本承担者

<!-- source-paragraph:V82-P3687 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3688 style=TableHead -->
字段

<!-- source-paragraph:V82-P3689 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3690 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3691 style=TableText -->
1. 人员与岗位

<!-- source-paragraph:V82-P3692 style=TableText -->
2. 程序

<!-- source-paragraph:V82-P3693 style=TableText -->
3. 预算

<!-- source-paragraph:V82-P3694 style=TableText -->
4. 基础设施

<!-- source-paragraph:V82-P3695 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3696 style=TableText -->
1. 各节点行为、决策、授权、监督与补救责任者

<!-- source-paragraph:V82-P3697 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3698 style=TableText -->
链条有效不证明目标正当

<!-- source-paragraph:V82-P3699 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3700 style=TableText -->
全链证据充分时至解释或诊断级

<!-- source-paragraph:V82-P3701 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3702 style=TableText -->
本变量只生成链条连通、时滞、损耗、中断、成本与承接需求描述，不授权减载、资源调整或试验；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3703 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3704 style=TableText -->
1. 强烈愿景和集中动员没有持续资源、维护或偿付

<!-- source-paragraph:V82-P3705 style=TableText -->
2. 表面贯通的链条把关键成本转移给边界外承接者

<!-- source-paragraph:V82-P3706 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3707 style=TableText -->
依appeal_and_rollback_rule，链上承接或受影响位置可经安全可达、反报复通道挑战资源、成本与链条归因，并触发与原链条判断或决策链独立的复核

<!-- source-paragraph:V82-P3708 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3709 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销整体链条归因及其下游效力、恢复为节点级描述与未决状态，保留版本与完成验证

<!-- source-paragraph:V82-P3710 style=SecH2 -->
A.7　HV07 反馈写回（完整接口卡）

<!-- source-paragraph:V82-P3711 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3712 style=TableHead -->
字段

<!-- source-paragraph:V82-P3713 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3714 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3715 style=TableText -->
HV07

<!-- source-paragraph:V82-P3716 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3717 style=TableText -->
human_variable:HV07

<!-- source-paragraph:V82-P3718 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3719 style=TableText -->
反馈写回

<!-- source-paragraph:V82-P3720 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3721 style=TableText -->
H

<!-- source-paragraph:V82-P3722 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3723 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3724 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3725 style=TableText -->
申诉、审计和反馈只有改变记录、规则、资源、角色、责任、记忆或停止条件时才构成人类制度写回。

<!-- source-paragraph:V82-P3726 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3727 style=TableText -->
具有反馈、申诉、审计或治理程序的人类结构

<!-- source-paragraph:V82-P3728 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3729 style=TableText -->
只有接收回执、表态或发布而无状态更新

<!-- source-paragraph:V82-P3730 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3731 style=TableHead -->
字段

<!-- source-paragraph:V82-P3732 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3733 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3734 style=TableText -->
1. D2

<!-- source-paragraph:V82-P3735 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3736 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P3737 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3738 style=TableText -->
1. H3

<!-- source-paragraph:V82-P3739 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3740 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3741 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3742 style=TableText -->
1. route_id=HV07-R0-writeback-classification；

<!-- source-paragraph:V82-P3743 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P3744 style=TableText -->
when=输入通道、回执、字段前后版本、执行记录、生效时间、持续时间及停止或回滚状态可分别检查。；

<!-- source-paragraph:V82-P3745 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3746 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3747 style=TableText -->
allowed_conclusion=区分未提交、已提交、已受理、字段改变、已执行、持续或失效的写回状态。；

<!-- source-paragraph:V82-P3748 style=TableText -->
result_ceiling=只有字段改变且实际执行才称制度性写回；一次写回不称学习。

<!-- source-paragraph:V82-P3749 style=TableText -->
2. route_id=HV07-R1-causal-feedback；

<!-- source-paragraph:V82-P3750 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P3751 style=TableText -->
when=符合资格的G2-instance显示制度返回通道相对无返回或阻断条件改变预选后续状态或转移。；

<!-- source-paragraph:V82-P3752 style=TableText -->
additional_inferential_requires=G2-instance；

<!-- source-paragraph:V82-P3753 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3754 style=TableText -->
allowed_conclusion=登记指定字段、通道和窗口内的有效反馈与制度写回效应。；

<!-- source-paragraph:V82-P3755 style=TableText -->
result_ceiling=不得从反馈存在推出学习、长期修复、正当性或授权扩大。

<!-- source-paragraph:V82-P3756 style=TableText -->
3. route_id=HV07-R2-feedback-mediated-learning；

<!-- source-paragraph:V82-P3757 style=TableText -->
claim_level=intertemporal_explanation；

<!-- source-paragraph:V82-P3758 style=TableText -->
when=有效反馈已有G2-instance支持，且G3-instance显示可保留更新在重复轮次对预定任务提供历史条件增量。；

<!-- source-paragraph:V82-P3759 style=TableText -->
additional_inferential_requires=G2-instance、G3-instance；

<!-- source-paragraph:V82-P3760 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3761 style=TableText -->
allowed_conclusion=登记限定任务、轮次和窗口内的反馈介导学习候选。；

<!-- source-paragraph:V82-P3762 style=TableText -->
result_ceiling=不得称整体制度已经学习、修复完成或价值方向正确。

<!-- source-paragraph:V82-P3763 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3764 style=TableText -->
1. 有效写回、阻塞写回与表面反馈

<!-- source-paragraph:V82-P3765 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3766 style=TableText -->
1. 有渠道即会学习

<!-- source-paragraph:V82-P3767 style=TableText -->
2. 一次更新即长期修复

<!-- source-paragraph:V82-P3768 style=TableText -->
3. 沉默即同意

<!-- source-paragraph:V82-P3769 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3770 style=TableHead -->
字段

<!-- source-paragraph:V82-P3771 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3772 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3773 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次反馈或申诉、写回个案、反馈总体、受理执行分布及聚合规则；X=空间范围：提交渠道、组织或平台边界、制度辖区与跨域申诉范围；T=时间跨度：提交、受理、字段变化、执行、持续与复核时滞；O=组织层级：反馈角色、受理团队、组织、制度至治理生态；C=因果层次：反馈事件、写回互动机制、中观程序结构、制度规则与系统条件；R=观察分辨率：原始反馈、处理序列、写回个案、结果分布、时效指标与摘要，并登记压缩损失；I=影响范围：直接申诉人与承接者、间接受影响者、二阶制度后果、跨域与代际影响；N=网络拓扑范围：反馈通道、受理节点、复核路径、阻塞点与跨层连接；J=管辖与授权范围：受理、字段修改、执行、停止、回滚与补救分别登记授权；登记跨层路径

<!-- source-paragraph:V82-P3774 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3775 style=TableText -->
改变后续制度状态或转移的返回通道

<!-- source-paragraph:V82-P3776 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3777 style=TableText -->
1. 反馈来源、通道、写回字段和后续变化

<!-- source-paragraph:V82-P3778 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3779 style=TableText -->
1. 反馈代表性

<!-- source-paragraph:V82-P3780 style=TableText -->
2. 跨层写回路径

<!-- source-paragraph:V82-P3781 style=TableText -->
3. 聚合损失

<!-- source-paragraph:V82-P3782 style=TableText -->
4. 外部复核

<!-- source-paragraph:V82-P3783 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3784 style=TableText -->
1. 写回载体、时滞和责任主体可改变

<!-- source-paragraph:V82-P3785 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3786 style=TableText -->
1. 无记录、规则、资源、角色或停止条件的过程

<!-- source-paragraph:V82-P3787 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3788 style=TableText -->
1. 个案反馈直接代表总体意见

<!-- source-paragraph:V82-P3789 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3790 style=TableHead -->
字段

<!-- source-paragraph:V82-P3791 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3792 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3793 style=TableText -->
1. 到达

<!-- source-paragraph:V82-P3794 style=TableText -->
2. 受理

<!-- source-paragraph:V82-P3795 style=TableText -->
3. 写回

<!-- source-paragraph:V82-P3796 style=TableText -->
4. 阻塞

<!-- source-paragraph:V82-P3797 style=TableText -->
5. 失真

<!-- source-paragraph:V82-P3798 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3799 style=TableText -->
1. 反馈或申诉的提交与受理凭证

<!-- source-paragraph:V82-P3800 style=TableText -->
2. 记录、规则、资源、角色、责任或停止条件的版本差异

<!-- source-paragraph:V82-P3801 style=TableText -->
3. 变更的执行记录、生效时间与持续时间

<!-- source-paragraph:V82-P3802 style=TableText -->
4. 复核、撤销、补救及后续状态变化

<!-- source-paragraph:V82-P3803 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3804 style=TableText -->
1. 反馈原文

<!-- source-paragraph:V82-P3805 style=TableText -->
2. 受理轨迹

<!-- source-paragraph:V82-P3806 style=TableText -->
3. 字段版本

<!-- source-paragraph:V82-P3807 style=TableText -->
4. 后续规则或资源变化

<!-- source-paragraph:V82-P3808 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3809 style=TableText -->
1. 反馈来源

<!-- source-paragraph:V82-P3810 style=TableText -->
2. 安全通道

<!-- source-paragraph:V82-P3811 style=TableText -->
3. 责任人

<!-- source-paragraph:V82-P3812 style=TableText -->
4. 复核程序

<!-- source-paragraph:V82-P3813 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3814 style=TableText -->
1. 记录、规则、资源、角色、责任、记忆或停止条件更新

<!-- source-paragraph:V82-P3815 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3816 style=TableText -->
登记提交、受理、决定、执行和复审时限

<!-- source-paragraph:V82-P3817 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3818 style=TableText -->
记录未达反馈、保护性匿名与不可见处理

<!-- source-paragraph:V82-P3819 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3820 style=TableText -->
无法安全提交、受反报复威胁或无数字接入的位置

<!-- source-paragraph:V82-P3821 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3822 style=TableText -->
1. 提交者

<!-- source-paragraph:V82-P3823 style=TableText -->
2. 被评价者

<!-- source-paragraph:V82-P3824 style=TableText -->
3. 执行者

<!-- source-paragraph:V82-P3825 style=TableText -->
4. 制度受益者

<!-- source-paragraph:V82-P3826 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3827 style=TableHead -->
字段

<!-- source-paragraph:V82-P3828 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3829 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3830 style=TableText -->
1. 申诉系统

<!-- source-paragraph:V82-P3831 style=TableText -->
2. 审计程序

<!-- source-paragraph:V82-P3832 style=TableText -->
3. 会议记录

<!-- source-paragraph:V82-P3833 style=TableText -->
4. 规则库

<!-- source-paragraph:V82-P3834 style=TableText -->
5. 责任链

<!-- source-paragraph:V82-P3835 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3836 style=TableText -->
1. 受理者

<!-- source-paragraph:V82-P3837 style=TableText -->
2. 决策者

<!-- source-paragraph:V82-P3838 style=TableText -->
3. 写回执行者

<!-- source-paragraph:V82-P3839 style=TableText -->
4. 监督者

<!-- source-paragraph:V82-P3840 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3841 style=TableText -->
反馈有效性与反馈内容正当性分别判断

<!-- source-paragraph:V82-P3842 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3843 style=TableText -->
确认写回字段和后续变化时至解释级

<!-- source-paragraph:V82-P3844 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3845 style=TableText -->
本变量只生成受理、字段变化、执行、持续时间与写回缺口描述，以及复核或程序修复需求，不授权改写记录规则、执行修复或关闭申诉；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3846 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3847 style=TableText -->
1. 申诉获得接收回执但记录、规则、资源和停止条件均未改变

<!-- source-paragraph:V82-P3848 style=TableText -->
2. 审计报告被发布却没有责任人、时限或后续状态更新

<!-- source-paragraph:V82-P3849 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3850 style=TableText -->
依appeal_and_rollback_rule，反馈提交者可经安全可达、反报复通道要求状态、时限、责任人与写回结果，并触发与原受理、写回或决策链独立的复核

<!-- source-paragraph:V82-P3851 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3852 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误更新，实际恢复先前记录、规则、资源、角色或停止条件状态，保留版本与完成验证

<!-- source-paragraph:V82-P3853 style=SecH2 -->
A.8　HV08 条件势场（完整接口卡）

<!-- source-paragraph:V82-P3854 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3855 style=TableHead -->
字段

<!-- source-paragraph:V82-P3856 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3857 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P3858 style=TableText -->
HV08

<!-- source-paragraph:V82-P3859 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P3860 style=TableText -->
human_variable:HV08

<!-- source-paragraph:V82-P3861 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P3862 style=TableText -->
条件势场

<!-- source-paragraph:V82-P3863 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P3864 style=TableText -->
H

<!-- source-paragraph:V82-P3865 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P3866 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P3867 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P3868 style=TableText -->
资源、制度、关系、权力、安全、指标、平台与历史条件只有通过可检测机制改变人类行动概率或约束时进入解释。

<!-- source-paragraph:V82-P3869 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P3870 style=TableText -->
人类行动受情境、制度与权力位置影响的场景

<!-- source-paragraph:V82-P3871 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P3872 style=TableText -->
势场被当作万能背景、意图主体或道德标签

<!-- source-paragraph:V82-P3873 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P3874 style=TableHead -->
字段

<!-- source-paragraph:V82-P3875 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3876 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P3877 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3878 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P3879 style=TableText -->
1. E2

<!-- source-paragraph:V82-P3880 style=TableText -->
2. EVIDENCE

<!-- source-paragraph:V82-P3881 style=TableText -->
3. SOURCE

<!-- source-paragraph:V82-P3882 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P3883 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3884 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P3885 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P3886 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P3887 style=TableText -->
1. route_id=HV08-R0-condition-inventory；

<!-- source-paragraph:V82-P3888 style=TableText -->
claim_level=candidate_description；

<!-- source-paragraph:V82-P3889 style=TableText -->
when=资源、规则、位置、安全、指标、平台、AI中介或历史沉积可按位置、尺度和时间窗列出，但尚无符合资格的H4-instance。；

<!-- source-paragraph:V82-P3890 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P3891 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P3892 style=TableText -->
allowed_conclusion=登记候选条件、位置异质性、观察盲区、竞争解释与补证需求。；

<!-- source-paragraph:V82-P3893 style=TableText -->
result_ceiling=仅称条件清单或候选通道；不得把条件人格化，也不得称权力、中介或反身效应已成立。

<!-- source-paragraph:V82-P3894 style=TableText -->
2. route_id=HV08-R1-position-or-mediation-effect；

<!-- source-paragraph:V82-P3895 style=TableText -->
claim_level=conditional_effect；

<!-- source-paragraph:V82-P3896 style=TableText -->
when=H4-instance在证据覆盖、表达安全或对象行为中唯一预选的成功判据取得supported。；

<!-- source-paragraph:V82-P3897 style=TableText -->
additional_inferential_requires=H4-instance；

<!-- source-paragraph:V82-P3898 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P3899 style=TableText -->
allowed_conclusion=登记该实例位置、中介、结果家族和窗口内的遮蔽、放大或行为响应通道。；

<!-- source-paragraph:V82-P3900 style=TableText -->
result_ceiling=不外推到未选结果家族，不从位置或中介效应推出恶意、责任或自动处置。

<!-- source-paragraph:V82-P3901 style=TableText -->
3. route_id=HV08-R2-reflexive-response；

<!-- source-paragraph:V82-P3902 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P3903 style=TableText -->
when=H4-instance唯一预选反身响应判据，且观测、命名、评分或发布经实际通道到达对象并取得supported。；

<!-- source-paragraph:V82-P3904 style=TableText -->
additional_inferential_requires=H4-instance；

<!-- source-paragraph:V82-P3905 style=TableText -->
additional_protocol_requires=E3、CAUSAL、E4；

<!-- source-paragraph:V82-P3906 style=TableText -->
allowed_conclusion=登记指定观测或发布通道与窗口内的反身响应。；

<!-- source-paragraph:V82-P3907 style=TableText -->
result_ceiling=一次响应不称持久反身性；不得据此隐藏观察、压制表达或扩大授权。

<!-- source-paragraph:V82-P3908 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P3909 style=TableText -->
1. 条件性机会、约束、遮蔽与放大

<!-- source-paragraph:V82-P3910 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P3911 style=TableText -->
1. 条件决定个体行为

<!-- source-paragraph:V82-P3912 style=TableText -->
2. 权力位置证明恶意

<!-- source-paragraph:V82-P3913 style=TableText -->
3. 环境具有意图

<!-- source-paragraph:V82-P3914 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P3915 style=TableHead -->
字段

<!-- source-paragraph:V82-P3916 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3917 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P3918 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次暴露或评价事件、位置个案、受条件总体、响应分布及聚合规则；X=空间范围：互动现场、组织或平台边界、公开数字空间与跨域环境；T=时间跨度：暴露积累、响应、反身变化与消退窗口；O=组织层级：行动与评价角色、团队、组织、制度至治理生态；C=因果层次：暴露事件、条件—行为互动机制、中观权力结构、制度规则与系统条件；R=观察分辨率：原始暴露表达行为、时间序列、位置个案、响应分布、平台指标与摘要，并登记压缩损失；I=影响范围：直接被评价者、间接受影响者、二阶反身后果、跨域与代际影响；N=网络拓扑范围：权力与信息连接、中介节点、遮蔽区、放大路径与跨域传播；J=管辖与授权范围：规则配置、指标使用、公开评价、人工复核与处置分别登记授权；比较位置异质性

<!-- source-paragraph:V82-P3919 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P3920 style=TableText -->
经实际通道改变行动概率、表达安全或证据分布的条件集合

<!-- source-paragraph:V82-P3921 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P3922 style=TableText -->
1. 条件到行为或证据的机制链

<!-- source-paragraph:V82-P3923 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P3924 style=TableText -->
1. 位置分布

<!-- source-paragraph:V82-P3925 style=TableText -->
2. 条件异质性

<!-- source-paragraph:V82-P3926 style=TableText -->
3. 跨域外部性

<!-- source-paragraph:V82-P3927 style=TableText -->
4. J轴

<!-- source-paragraph:V82-P3928 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P3929 style=TableText -->
1. 关键条件与作用强度可随尺度改变

<!-- source-paragraph:V82-P3930 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P3931 style=TableText -->
1. 无意向行动、权力或制度位置的非人系统

<!-- source-paragraph:V82-P3932 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P3933 style=TableText -->
1. 局部条件直接普遍化为所有主体的动机

<!-- source-paragraph:V82-P3934 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P3935 style=TableHead -->
字段

<!-- source-paragraph:V82-P3936 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3937 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P3938 style=TableText -->
1. 支持

<!-- source-paragraph:V82-P3939 style=TableText -->
2. 约束

<!-- source-paragraph:V82-P3940 style=TableText -->
3. 遮蔽

<!-- source-paragraph:V82-P3941 style=TableText -->
4. 放大

<!-- source-paragraph:V82-P3942 style=TableText -->
5. 混合

<!-- source-paragraph:V82-P3943 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P3944 style=TableText -->
1. 资源、规则、平台或公开条件改变前后的行为差异

<!-- source-paragraph:V82-P3945 style=TableText -->
2. 不同位置的表达安全、证据覆盖和缺席率

<!-- source-paragraph:V82-P3946 style=TableText -->
3. 指标、评分或AI中介前后的可见性与处置变化

<!-- source-paragraph:V82-P3947 style=TableText -->
4. 比较条件下候选通道效应是否超过预定阈值

<!-- source-paragraph:V82-P3948 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P3949 style=TableText -->
1. 资源与规则

<!-- source-paragraph:V82-P3950 style=TableText -->
2. 位置差异

<!-- source-paragraph:V82-P3951 style=TableText -->
3. 平台或指标变化

<!-- source-paragraph:V82-P3952 style=TableText -->
4. 行为响应

<!-- source-paragraph:V82-P3953 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P3954 style=TableText -->
1. 边界与接口2. 观察位置3. 因果合同

<!-- source-paragraph:V82-P3955 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P3956 style=TableText -->
1. 可行路径2. 表达和证据3. 生成与失稳

<!-- source-paragraph:V82-P3957 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P3958 style=TableText -->
登记条件积累、响应与消退时滞

<!-- source-paragraph:V82-P3959 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P3960 style=TableText -->
记录不可观察条件、共线性和反身变化

<!-- source-paragraph:V82-P3961 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P3962 style=TableText -->
因安全、身份或平台门槛而不可见的位置

<!-- source-paragraph:V82-P3963 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P3964 style=TableText -->
1. 优势位置

<!-- source-paragraph:V82-P3965 style=TableText -->
2. 低权力位置

<!-- source-paragraph:V82-P3966 style=TableText -->
3. 中介者

<!-- source-paragraph:V82-P3967 style=TableText -->
4. 被评价者

<!-- source-paragraph:V82-P3968 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P3969 style=TableHead -->
字段

<!-- source-paragraph:V82-P3970 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P3971 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P3972 style=TableText -->
1. 制度

<!-- source-paragraph:V82-P3973 style=TableText -->
2. 资源配置

<!-- source-paragraph:V82-P3974 style=TableText -->
3. 平台

<!-- source-paragraph:V82-P3975 style=TableText -->
4. 指标

<!-- source-paragraph:V82-P3976 style=TableText -->
5. 关系网络

<!-- source-paragraph:V82-P3977 style=TableText -->
6. 历史沉积

<!-- source-paragraph:V82-P3978 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P3979 style=TableText -->
1. 规则制定者

<!-- source-paragraph:V82-P3980 style=TableText -->
2. 平台运营者

<!-- source-paragraph:V82-P3981 style=TableText -->
3. 资源配置者

<!-- source-paragraph:V82-P3982 style=TableText -->
4. 行动决策者

<!-- source-paragraph:V82-P3983 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P3984 style=TableText -->
条件优势或筛选结果不构成正当性

<!-- source-paragraph:V82-P3985 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P3986 style=TableText -->
机制链与反事实充分时至解释级

<!-- source-paragraph:V82-P3987 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P3988 style=TableText -->
本变量只生成候选条件通道、位置异质性、证据遮蔽与风险降低需求描述，不授权改变规则平台、资源配置、评价或处置主体；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P3989 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P3990 style=TableText -->
1. 相同制度条件下不同安全和权力位置出现相反行动

<!-- source-paragraph:V82-P3991 style=TableText -->
2. 以权力或平台标签替代实际因果通道后无法解释状态变化

<!-- source-paragraph:V82-P3992 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P3993 style=TableText -->
依appeal_and_rollback_rule，不同位置可经安全可达、反报复通道提交机制差异、缺席信号与安全影响，并触发与原势场判断或决策链独立的复核

<!-- source-paragraph:V82-P3994 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P3995 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销不成立的势场归因、移除位置标签及其下游评价处置效力并恢复未决状态，保留版本与完成验证

<!-- source-paragraph:V82-P3996 style=SecH2 -->
A.9　HV09 结构负荷（完整接口卡）

<!-- source-paragraph:V82-P3997 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P3998 style=TableHead -->
字段

<!-- source-paragraph:V82-P3999 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4000 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P4001 style=TableText -->
HV09

<!-- source-paragraph:V82-P4002 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P4003 style=TableText -->
human_variable:HV09

<!-- source-paragraph:V82-P4004 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P4005 style=TableText -->
结构负荷

<!-- source-paragraph:V82-P4006 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P4007 style=TableText -->
H

<!-- source-paragraph:V82-P4008 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P4009 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P4010 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P4011 style=TableText -->
人类结构负荷必须把任务、协调损耗、维护要求、容量、恢复余量和成本承担位置共同登记。

<!-- source-paragraph:V82-P4012 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P4013 style=TableText -->
持续运转、维护、照护或高压条件下的人类结构

<!-- source-paragraph:V82-P4014 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P4015 style=TableText -->
只用熵、脆弱或韧性隐喻而无任务、容量和恢复机制

<!-- source-paragraph:V82-P4016 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P4017 style=TableHead -->
字段

<!-- source-paragraph:V82-P4018 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4019 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P4020 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4021 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P4022 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P4023 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P4024 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4025 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P4026 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4027 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P4028 style=TableText -->
1. route_id=HV09-R0-instant-task-capacity；

<!-- source-paragraph:V82-P4029 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P4030 style=TableText -->
when=同一窗口、位置与类型映射下的任务或协调要求、容量、恢复余量及其分布可观察。；

<!-- source-paragraph:V82-P4031 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P4032 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P4033 style=TableText -->
allowed_conclusion=登记瞬时任务—容量关系、余量、积压、局部缺口与恢复状态。；

<!-- source-paragraph:V82-P4034 style=TableText -->
result_ceiling=只到同窗描述；瞬时峰值或缺口不自动成为过载机制、累积损伤或崩溃。

<!-- source-paragraph:V82-P4035 style=TableText -->
2. route_id=HV09-R1-overload-mechanism；

<!-- source-paragraph:V82-P4036 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P4037 style=TableText -->
when=CM-LOAD的适用条件完整，且符合资格的G2-instance显示负荷、补给、减载或恢复通道对预选结果有超过阈值效应。；

<!-- source-paragraph:V82-P4038 style=TableText -->
additional_inferential_requires=G2-instance、CM-LOAD；

<!-- source-paragraph:V82-P4039 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P4040 style=TableText -->
allowed_conclusion=登记指定位置、类型、窗口和通道内的过载或恢复机制候选。；

<!-- source-paragraph:V82-P4041 style=TableText -->
result_ceiling=不得普遍化为熵、韧性或所有位置必然崩溃，也不直接生成减载或牺牲义务。

<!-- source-paragraph:V82-P4042 style=TableText -->
3. route_id=HV09-R2-cumulative-overload；

<!-- source-paragraph:V82-P4043 style=TableText -->
claim_level=intertemporal_explanation；

<!-- source-paragraph:V82-P4044 style=TableText -->
when=过载机制已有G2-instance与CM-LOAD支持，且G3-instance显示历史负荷对后续容量、错误或恢复具有条件增量。；

<!-- source-paragraph:V82-P4045 style=TableText -->
additional_inferential_requires=G2-instance、CM-LOAD、G3-instance；

<!-- source-paragraph:V82-P4046 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P4047 style=TableText -->
allowed_conclusion=登记预注册载体、窗口和结果内的累积损伤或迟恢复候选。；

<!-- source-paragraph:V82-P4048 style=TableText -->
result_ceiling=不推出不可逆、必然崩溃、责任归属或具名主体承担义务。

<!-- source-paragraph:V82-P4049 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P4050 style=TableText -->
1. 候选过载、余量不足、维护缺口与恢复差异

<!-- source-paragraph:V82-P4051 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P4052 style=TableText -->
1. 承接者应继续承担

<!-- source-paragraph:V82-P4053 style=TableText -->
2. 高负荷证明奉献

<!-- source-paragraph:V82-P4054 style=TableText -->
3. 过载主体等于失稳机制

<!-- source-paragraph:V82-P4055 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P4056 style=TableHead -->
字段

<!-- source-paragraph:V82-P4057 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4058 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P4059 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务负荷、承接个案、岗位或群体总体、负荷容量分布及聚合规则；X=空间范围：工作或照护现场、组织边界、数字劳动空间与跨域外包范围；T=时间跨度：瞬时峰值、持续积压、恢复时滞、跨期与代际窗口；O=组织层级：承接角色、团队、组织、制度至治理生态；C=因果层次：任务事件、任务—容量互动机制、中观瓶颈结构、制度分配与系统条件；R=观察分辨率：原始任务工时记录、负荷序列、承接个案、容量分布、时延错误指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接替代者、二阶外溢、跨域与代际成本；N=网络拓扑范围：任务依赖、关键瓶颈、替代节点、恢复路径与跨域外包网络；J=管辖与授权范围：任务分配、资源调整、停止、绩效使用与补救分别登记授权；保留负荷容量分布

<!-- source-paragraph:V82-P4060 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P4061 style=TableText -->
给定窗口内任务和协调要求相对可用容量与恢复余量的结构关系

<!-- source-paragraph:V82-P4062 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P4063 style=TableText -->
1. 负荷、容量、恢复与成本位置

<!-- source-paragraph:V82-P4064 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P4065 style=TableText -->
1. 负荷分布

<!-- source-paragraph:V82-P4066 style=TableText -->
2. 聚合遮蔽

<!-- source-paragraph:V82-P4067 style=TableText -->
3. 责任继承

<!-- source-paragraph:V82-P4068 style=TableText -->
4. 代际影响

<!-- source-paragraph:V82-P4069 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P4070 style=TableText -->
1. 瓶颈、容量和恢复方式可随层级改变

<!-- source-paragraph:V82-P4071 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P4072 style=TableText -->
1. 无持续非平衡、维护或人类承接要求的过程

<!-- source-paragraph:V82-P4073 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P4074 style=TableText -->
1. 平均负荷掩盖局部过载

<!-- source-paragraph:V82-P4075 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P4076 style=TableHead -->
字段

<!-- source-paragraph:V82-P4077 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4078 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P4079 style=TableText -->
1. 低负荷

<!-- source-paragraph:V82-P4080 style=TableText -->
2. 可承受

<!-- source-paragraph:V82-P4081 style=TableText -->
3. 临界

<!-- source-paragraph:V82-P4082 style=TableText -->
4. 过载

<!-- source-paragraph:V82-P4083 style=TableText -->
5. 恢复

<!-- source-paragraph:V82-P4084 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P4085 style=TableText -->
1. 单位时间任务量、积压、时延和错误率

<!-- source-paragraph:V82-P4086 style=TableText -->
2. 人员资源容量、隐性劳动与替代可用性

<!-- source-paragraph:V82-P4087 style=TableText -->
3. 停止、缺席、退出和恢复曲线

<!-- source-paragraph:V82-P4088 style=TableText -->
4. 平均负荷与关键局部承接位置的分布差异

<!-- source-paragraph:V82-P4089 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P4090 style=TableText -->
1. 任务量

<!-- source-paragraph:V82-P4091 style=TableText -->
2. 时延与错误

<!-- source-paragraph:V82-P4092 style=TableText -->
3. 人员与资源

<!-- source-paragraph:V82-P4093 style=TableText -->
4. 恢复记录

<!-- source-paragraph:V82-P4094 style=TableText -->
5. 退出和缺席

<!-- source-paragraph:V82-P4095 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P4096 style=TableText -->
1. 承接层

<!-- source-paragraph:V82-P4097 style=TableText -->
2. 动力—承接链

<!-- source-paragraph:V82-P4098 style=TableText -->
3. 条件势场

<!-- source-paragraph:V82-P4099 style=TableText -->
4. 瞬时负荷只调用G2与CM-LOAD；累积损伤、迟恢复或历史条件增量另需预注册G3-instance，H5候选留痕不能替代G3

<!-- source-paragraph:V82-P4100 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P4101 style=TableText -->
1. 状态更新2. 失稳行为3. 维护和修复需求

<!-- source-paragraph:V82-P4102 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P4103 style=TableText -->
区分即时峰值、持续积压、恢复时滞与代际成本

<!-- source-paragraph:V82-P4104 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P4105 style=TableText -->
记录隐性劳动、外包成本和保护性缺席

<!-- source-paragraph:V82-P4106 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P4107 style=TableText -->
非正式劳动、家庭照护、外包和低可见承接位置

<!-- source-paragraph:V82-P4108 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P4109 style=TableText -->
1. 承接者

<!-- source-paragraph:V82-P4110 style=TableText -->
2. 依赖服务者

<!-- source-paragraph:V82-P4111 style=TableText -->
3. 替代者

<!-- source-paragraph:V82-P4112 style=TableText -->
4. 成本外溢位置

<!-- source-paragraph:V82-P4113 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P4114 style=TableHead -->
字段

<!-- source-paragraph:V82-P4115 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4116 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P4117 style=TableText -->
1. 人员

<!-- source-paragraph:V82-P4118 style=TableText -->
2. 岗位

<!-- source-paragraph:V82-P4119 style=TableText -->
3. 程序

<!-- source-paragraph:V82-P4120 style=TableText -->
4. 设施

<!-- source-paragraph:V82-P4121 style=TableText -->
5. 预算

<!-- source-paragraph:V82-P4122 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P4123 style=TableText -->
1. 任务分配者

<!-- source-paragraph:V82-P4124 style=TableText -->
2. 资源配置者

<!-- source-paragraph:V82-P4125 style=TableText -->
3. 授权者

<!-- source-paragraph:V82-P4126 style=TableText -->
4. 监督者

<!-- source-paragraph:V82-P4127 style=TableText -->
5. 补救责任者

<!-- source-paragraph:V82-P4128 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P4129 style=TableText -->
高效率或高承载不构成正当性

<!-- source-paragraph:V82-P4130 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P4131 style=TableText -->
负荷容量和恢复证据充分时至诊断级

<!-- source-paragraph:V82-P4132 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P4133 style=TableText -->
本变量只生成负荷、容量、恢复、局部过载与减载补资源需求描述，不授权任务削减、资源投入、绩效处置或强迫承担；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P4134 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P4135 style=TableText -->
1. 总体平均容量充足但少数关键承接位置持续过载

<!-- source-paragraph:V82-P4136 style=TableText -->
2. 只用熵或韧性隐喻却无法识别任务、容量和恢复通道

<!-- source-paragraph:V82-P4137 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P4138 style=TableText -->
依appeal_and_rollback_rule，承接者可经安全可达、反报复通道报告隐性劳动、过载和恢复需求，并触发与原负荷判断、绩效或任务决策链独立的复核

<!-- source-paragraph:V82-P4139 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P4140 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误负荷判断及绩效或责任效力，实际恢复任务、资源与记录状态，保留版本与完成验证

<!-- source-paragraph:V82-P4141 style=SecH2 -->
A.10　HV10 演化相位（完整接口卡）

<!-- source-paragraph:V82-P4142 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P4143 style=TableHead -->
字段

<!-- source-paragraph:V82-P4144 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4145 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P4146 style=TableText -->
HV10

<!-- source-paragraph:V82-P4147 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P4148 style=TableText -->
human_variable:HV10

<!-- source-paragraph:V82-P4149 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P4150 style=TableText -->
演化相位

<!-- source-paragraph:V82-P4151 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P4152 style=TableText -->
H

<!-- source-paragraph:V82-P4153 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P4154 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P4155 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P4156 style=TableText -->
S0-S6和X0只适用于存在方向、生成主体或事件、承接层与制度化过程的人类意向性集体，且允许跳阶、并行、混合、回退、分裂、合并、休眠、吞并和功能转移。

<!-- source-paragraph:V82-P4157 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P4158 style=TableText -->
符合适用条件的人类意向性集体

<!-- source-paragraph:V82-P4159 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P4160 style=TableText -->
适用条件缺失、阶段被道德化或标题与判据不一致

<!-- source-paragraph:V82-P4161 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P4162 style=TableHead -->
字段

<!-- source-paragraph:V82-P4163 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4164 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P4165 style=TableText -->
1. human_variable:HV03

<!-- source-paragraph:V82-P4166 style=TableText -->
2. human_variable:HV04

<!-- source-paragraph:V82-P4167 style=TableText -->
3. human_variable:HV05

<!-- source-paragraph:V82-P4168 style=TableText -->
4. human_variable:HV07

<!-- source-paragraph:V82-P4169 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P4170 style=TableText -->
1. EVIDENCE2. SOURCE

<!-- source-paragraph:V82-P4171 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P4172 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4173 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P4174 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4175 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P4176 style=TableText -->
1. route_id=HV10-R0-component-applicability；

<!-- source-paragraph:V82-P4177 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P4178 style=TableText -->
when=HV03、HV04、HV05与HV07已有可审计评估记录；记录允许为missing、not_applicable或unsupported，不要求四组件经验成立。；

<!-- source-paragraph:V82-P4179 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P4180 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P4181 style=TableText -->
allowed_conclusion=登记适用、不适用、组件缺失、混合状态与继续观察需求。；

<!-- source-paragraph:V82-P4182 style=TableText -->
result_ceiling=组件检查本身不产生S0-S6或X0相位匹配。

<!-- source-paragraph:V82-P4183 style=TableText -->
2. route_id=HV10-R1-pattern-phase-match；

<!-- source-paragraph:V82-P4184 style=TableText -->
claim_level=descriptive_classification；

<!-- source-paragraph:V82-P4185 style=TableText -->
when=CM-PHASE的状态判据、观察窗、混合与转换规则完整，并在重复窗口匹配。；

<!-- source-paragraph:V82-P4186 style=TableText -->
additional_inferential_requires=CM-PHASE；

<!-- source-paragraph:V82-P4187 style=TableText -->
additional_protocol_requires=E4；

<!-- source-paragraph:V82-P4188 style=TableText -->
allowed_conclusion=登记S0-S6或X0的原型匹配、混合、并行、回退、休眠或转换描述。；

<!-- source-paragraph:V82-P4189 style=TableText -->
result_ceiling=只到模式相位；相位不是健康、成功、正当性或淘汰等级。

<!-- source-paragraph:V82-P4190 style=TableText -->
3. route_id=HV10-R2-causal-transition；

<!-- source-paragraph:V82-P4191 style=TableText -->
claim_level=mechanism_explanation；

<!-- source-paragraph:V82-P4192 style=TableText -->
when=CM-PHASE匹配成立，且G2-instance识别指定相位转移通道对预选状态变化的效应。；

<!-- source-paragraph:V82-P4193 style=TableText -->
additional_inferential_requires=CM-PHASE、G2-instance；

<!-- source-paragraph:V82-P4194 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P4195 style=TableText -->
allowed_conclusion=登记指定对象、窗口和通道内的候选因果相位转移。；

<!-- source-paragraph:V82-P4196 style=TableText -->
result_ceiling=不得从转移机制推出必然阶段序列、价值方向或推进与淘汰授权。

<!-- source-paragraph:V82-P4197 style=TableText -->
4. route_id=HV10-R3-path-dependent-phase；

<!-- source-paragraph:V82-P4198 style=TableText -->
claim_level=intertemporal_explanation；

<!-- source-paragraph:V82-P4199 style=TableText -->
when=CM-PHASE匹配成立，且G3-instance显示历史相位变量对后续状态、迟滞或回退具有条件增量。；

<!-- source-paragraph:V82-P4200 style=TableText -->
additional_inferential_requires=CM-PHASE、G3-instance；

<!-- source-paragraph:V82-P4201 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P4202 style=TableText -->
allowed_conclusion=登记预注册窗口内的路径依赖、迟滞或历史相位差异候选。；

<!-- source-paragraph:V82-P4203 style=TableText -->
result_ceiling=不得称命运、绝对不可逆或自动规定修复、退出与退场方案。

<!-- source-paragraph:V82-P4204 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P4205 style=TableText -->
1. 条件性状态坐标

<!-- source-paragraph:V82-P4206 style=TableText -->
2. 非线性路径

<!-- source-paragraph:V82-P4207 style=TableText -->
3. 有序退场X0

<!-- source-paragraph:V82-P4208 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P4209 style=TableText -->
1. 所有系统必经S0-S6

<!-- source-paragraph:V82-P4210 style=TableText -->
2. 阶段越高越正当

<!-- source-paragraph:V82-P4211 style=TableText -->
3. 解体等于失败

<!-- source-paragraph:V82-P4212 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P4213 style=TableHead -->
字段

<!-- source-paragraph:V82-P4214 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4215 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P4216 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次状态事件、局部群体个案、意向集体总体、相位分布及聚合规则；X=空间范围：行动现场、组织或制度边界、数字协作空间与跨域演化范围；T=时间跨度：状态窗口、转移时滞、回退、休眠、迟滞与代际周期；O=组织层级：成员角色、团队、组织、制度至治理生态；C=因果层次：状态事件、转移互动机制、中观相位结构、制度化过程与系统条件；R=观察分辨率：原始状态事件、转移序列、局部个案、相位分布、状态指标与摘要，并登记压缩损失；I=影响范围：直接成员与承接者、退出者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：局部相位簇群、跨层连接、分裂合并、功能转移与继承路径；J=管辖与授权范围：相位命名、监测采用、试探、推进、退场与淘汰分别登记授权；保留混合相位

<!-- source-paragraph:V82-P4217 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P4218 style=TableText -->
具有人类意向、生成、承接和制度化的集体状态

<!-- source-paragraph:V82-P4219 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P4220 style=TableText -->
1. 适用条件

<!-- source-paragraph:V82-P4221 style=TableText -->
2. 相位判据

<!-- source-paragraph:V82-P4222 style=TableText -->
3. 非线性路径

<!-- source-paragraph:V82-P4223 style=TableText -->
4. X0不计为第八阶段

<!-- source-paragraph:V82-P4224 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P4225 style=TableText -->
1. 局部相位分布

<!-- source-paragraph:V82-P4226 style=TableText -->
2. 跨层转移

<!-- source-paragraph:V82-P4227 style=TableText -->
3. 承接继承

<!-- source-paragraph:V82-P4228 style=TableText -->
4. 保护与退出

<!-- source-paragraph:V82-P4229 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P4230 style=TableText -->
1. 承接者、制度载体和有效对象可随相位改变

<!-- source-paragraph:V82-P4231 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P4232 style=TableText -->
1. 无方向、生成、承接或制度化过程的系统

<!-- source-paragraph:V82-P4233 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P4234 style=TableText -->
1. 个案相位直接代表总体

<!-- source-paragraph:V82-P4235 style=TableText -->
2. 人类阶段迁入通用核心

<!-- source-paragraph:V82-P4236 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P4237 style=TableHead -->
字段

<!-- source-paragraph:V82-P4238 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4239 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P4240 style=TableText -->
1. S0

<!-- source-paragraph:V82-P4241 style=TableText -->
2. S1

<!-- source-paragraph:V82-P4242 style=TableText -->
3. S2

<!-- source-paragraph:V82-P4243 style=TableText -->
4. S3

<!-- source-paragraph:V82-P4244 style=TableText -->
5. S4

<!-- source-paragraph:V82-P4245 style=TableText -->
6. S5

<!-- source-paragraph:V82-P4246 style=TableText -->
7. S6

<!-- source-paragraph:V82-P4247 style=TableText -->
8. X0转换路径

<!-- source-paragraph:V82-P4248 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P4249 style=TableText -->
1. 方向、生成、承接、制度化和反馈变量的同期状态

<!-- source-paragraph:V82-P4250 style=TableText -->
2. 相位判据跨观察窗的重复匹配记录

<!-- source-paragraph:V82-P4251 style=TableText -->
3. 跳阶、并行、混合、回退、分裂、合并与休眠轨迹

<!-- source-paragraph:V82-P4252 style=TableText -->
4. X0中的功能转移、责任继承与有序退场记录

<!-- source-paragraph:V82-P4253 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P4254 style=TableText -->
1. 相位变量

<!-- source-paragraph:V82-P4255 style=TableText -->
2. 转移记录

<!-- source-paragraph:V82-P4256 style=TableText -->
3. 留痕

<!-- source-paragraph:V82-P4257 style=TableText -->
4. 承接与制度状态

<!-- source-paragraph:V82-P4258 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P4259 style=TableText -->
1. 指向锚点

<!-- source-paragraph:V82-P4260 style=TableText -->
2. 生成节点

<!-- source-paragraph:V82-P4261 style=TableText -->
3. 承接层

<!-- source-paragraph:V82-P4262 style=TableText -->
4. 反馈写回

<!-- source-paragraph:V82-P4263 style=TableText -->
5. 结构负荷

<!-- source-paragraph:V82-P4264 style=TableText -->
6. 模式相位不要求G3；因果转移另需CAUSAL；迟滞、路径依赖或历史效应另需预注册G3-instance，H5只登记候选留痕

<!-- source-paragraph:V82-P4265 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P4266 style=TableText -->
1. 相位判断2. 承接继承3. 退场和修复需求

<!-- source-paragraph:V82-P4267 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P4268 style=TableText -->
登记相位观察窗、转移时滞、回退与休眠

<!-- source-paragraph:V82-P4269 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P4270 style=TableText -->
记录混合相位、分裂、合并与尺度差异

<!-- source-paragraph:V82-P4271 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P4272 style=TableText -->
总体相位无法代表的局部群体和角色

<!-- source-paragraph:V82-P4273 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P4274 style=TableText -->
1. 成员

<!-- source-paragraph:V82-P4275 style=TableText -->
2. 承接者

<!-- source-paragraph:V82-P4276 style=TableText -->
3. 异议者

<!-- source-paragraph:V82-P4277 style=TableText -->
4. 退出者

<!-- source-paragraph:V82-P4278 style=TableText -->
5. 继承者

<!-- source-paragraph:V82-P4279 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P4280 style=TableHead -->
字段

<!-- source-paragraph:V82-P4281 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4282 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P4283 style=TableText -->
1. 集体行动

<!-- source-paragraph:V82-P4284 style=TableText -->
2. 组织结构

<!-- source-paragraph:V82-P4285 style=TableText -->
3. 制度记录

<!-- source-paragraph:V82-P4286 style=TableText -->
4. 共同记忆

<!-- source-paragraph:V82-P4287 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P4288 style=TableText -->
1. 作出相位判断的分析者

<!-- source-paragraph:V82-P4289 style=TableText -->
2. 据此行动的决策与授权者

<!-- source-paragraph:V82-P4290 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P4291 style=TableText -->
相位不构成健康、成功或正当性等级

<!-- source-paragraph:V82-P4292 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P4293 style=TableText -->
适用条件和相位证据充分时至原型匹配级

<!-- source-paragraph:V82-P4294 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P4295 style=TableText -->
本变量只生成相位原型匹配、混合状态、不确定性与观察需求描述，不授权试探、推进、合并、退场或淘汰；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P4296 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P4297 style=TableText -->
1. 同一集体同时呈现S2承接成形与S5漏洞积累的混合相位

<!-- source-paragraph:V82-P4298 style=TableText -->
2. 有序退场X0保持功能转移而不是阶段失败

<!-- source-paragraph:V82-P4299 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P4300 style=TableText -->
依appeal_and_rollback_rule，成员可经安全可达、反报复通道挑战相位证据、线性假设和道德化使用，并触发与原相位判断或决策链独立的复核

<!-- source-paragraph:V82-P4301 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P4302 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销相位命名及其下游决策效力、实际恢复变量级描述与未决状态，保留版本与完成验证

<!-- source-paragraph:V82-P4303 style=SecH2 -->
A.11　HV11 开放性承担行动（完整接口卡）

<!-- source-paragraph:V82-P4304 style=CardLabel -->
A. 身份、命题与适用范围

<!-- source-paragraph:V82-P4305 style=TableHead -->
字段

<!-- source-paragraph:V82-P4306 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4307 style=TableText -->
接口 ID（id）

<!-- source-paragraph:V82-P4308 style=TableText -->
HV11

<!-- source-paragraph:V82-P4309 style=TableText -->
限定 ID（qualified_id）

<!-- source-paragraph:V82-P4310 style=TableText -->
human_variable:HV11

<!-- source-paragraph:V82-P4311 style=TableText -->
名称（name）

<!-- source-paragraph:V82-P4312 style=TableText -->
开放性承担行动

<!-- source-paragraph:V82-P4313 style=TableText -->
主张类型（claim_type）

<!-- source-paragraph:V82-P4314 style=TableText -->
H

<!-- source-paragraph:V82-P4315 style=TableText -->
合同角色（contract_role）

<!-- source-paragraph:V82-P4316 style=TableText -->
human_variable_interface

<!-- source-paragraph:V82-P4317 style=TableText -->
命题（proposition）

<!-- source-paragraph:V82-P4318 style=TableText -->
开放性承担只观察真实成本、自愿性、方向、替代解释和结构后果，不诊断某人有没有爱。

<!-- source-paragraph:V82-P4319 style=TableText -->
适用范围（scope）

<!-- source-paragraph:V82-P4320 style=TableText -->
人类关系、组织、制度与公共行动中的承担

<!-- source-paragraph:V82-P4321 style=TableText -->
暂停条件（pause_condition）

<!-- source-paragraph:V82-P4322 style=TableText -->
无法安全确认自愿、拒绝和退出，或分析转向人格与爱的诊断

<!-- source-paragraph:V82-P4323 style=CardLabel -->
B. 正式依赖与推论边界

<!-- source-paragraph:V82-P4324 style=TableHead -->
字段

<!-- source-paragraph:V82-P4325 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4326 style=TableText -->
推论依赖（inferential_requires）

<!-- source-paragraph:V82-P4327 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4328 style=TableText -->
协议依赖（protocol_requires）

<!-- source-paragraph:V82-P4329 style=TableText -->
1. N4

<!-- source-paragraph:V82-P4330 style=TableText -->
2. EVIDENCE

<!-- source-paragraph:V82-P4331 style=TableText -->
3. SOURCE

<!-- source-paragraph:V82-P4332 style=TableText -->
限定／特化（specializes）

<!-- source-paragraph:V82-P4333 style=TableText -->
1. H62. H2

<!-- source-paragraph:V82-P4334 style=TableText -->
适用对象引用（applies_to）

<!-- source-paragraph:V82-P4335 style=TableText -->
无（空集合）

<!-- source-paragraph:V82-P4336 style=TableText -->
条件支持路由（conditional_support_routes）

<!-- source-paragraph:V82-P4337 style=TableText -->
1. route_id=HV11-R0-action-cost-record；

<!-- source-paragraph:V82-P4338 style=TableText -->
claim_level=normative_boundary；

<!-- source-paragraph:V82-P4339 style=TableText -->
when=行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；

<!-- source-paragraph:V82-P4340 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P4341 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P4342 style=TableText -->
allowed_conclusion=描述候选承担行动、成本分布、强制风险、停止权缺口与保护需求。；

<!-- source-paragraph:V82-P4343 style=TableText -->
result_ceiling=不得称开放性承担，不得诊断爱、人格或要求继续承担。

<!-- source-paragraph:V82-P4344 style=TableText -->
2. route_id=HV11-R1-voluntary-limited-action；

<!-- source-paragraph:V82-P4345 style=TableText -->
claim_level=normative_boundary；

<!-- source-paragraph:V82-P4346 style=TableText -->
when=真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；

<!-- source-paragraph:V82-P4347 style=TableText -->
additional_inferential_requires=无（空集合）；

<!-- source-paragraph:V82-P4348 style=TableText -->
additional_protocol_requires=无（空集合）；

<!-- source-paragraph:V82-P4349 style=TableText -->
allowed_conclusion=登记有限、自愿且具有方向和可观察后果的开放性承担行动描述。；

<!-- source-paragraph:V82-P4350 style=TableText -->
result_ceiling=只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。

<!-- source-paragraph:V82-P4351 style=TableText -->
3. route_id=HV11-R2-structural-consequence；

<!-- source-paragraph:V82-P4352 style=TableText -->
claim_level=conditional_effect；

<!-- source-paragraph:V82-P4353 style=TableText -->
when=符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；

<!-- source-paragraph:V82-P4354 style=TableText -->
additional_inferential_requires=G2-instance；

<!-- source-paragraph:V82-P4355 style=TableText -->
additional_protocol_requires=CAUSAL、E4；

<!-- source-paragraph:V82-P4356 style=TableText -->
allowed_conclusion=登记指定通道、对象与窗口内的行动结构后果。；

<!-- source-paragraph:V82-P4357 style=TableText -->
result_ceiling=结构效应不证明爱、善、正当性、无限责任或行动授权。

<!-- source-paragraph:V82-P4358 style=TableText -->
允许推论（allowed_inference）

<!-- source-paragraph:V82-P4359 style=TableText -->
1. 描述有限承担行动与后果

<!-- source-paragraph:V82-P4360 style=TableText -->
禁止跳跃（prohibited_leap）

<!-- source-paragraph:V82-P4361 style=TableText -->
1. 诊断有没有爱

<!-- source-paragraph:V82-P4362 style=TableText -->
2. 牺牲等于爱

<!-- source-paragraph:V82-P4363 style=TableText -->
3. 责任等于无限承担

<!-- source-paragraph:V82-P4364 style=TableText -->
4. 拒绝等于道德失败

<!-- source-paragraph:V82-P4365 style=CardLabel -->
C. 九轴尺度与对象合同

<!-- source-paragraph:V82-P4366 style=TableHead -->
字段

<!-- source-paragraph:V82-P4367 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4368 style=TableText -->
九轴尺度画像（scale_profile）

<!-- source-paragraph:V82-P4369 style=TableText -->
SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次承担行动、行动者个案、关系或组织总体、成本自愿性分布及聚合规则；X=空间范围：关系与照护现场、组织边界、数字公共空间与跨域受益范围；T=时间跨度：即时行动、持续承担、耗竭、恢复与代际窗口；O=组织层级：行动角色、关系或团队、组织、制度至治理生态；C=因果层次：承担事件、行动—成本互动机制、中观关系结构、制度责任安排与系统条件；R=观察分辨率：原始行动与成本、承担序列、行动者个案、成本自愿性分布、后果指标与摘要，并登记压缩损失；I=影响范围：直接行动者与受益者、依赖者、间接替代承接者、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖照护、受益连接、替代承接、退出路径与跨域成本网络；J=管辖与授权范围：承担要求、资源使用、拒绝、停止、保护与补救分别登记授权；保留自愿成本退出差异

<!-- source-paragraph:V82-P4370 style=TableText -->
有效对象（effective_object）

<!-- source-paragraph:V82-P4371 style=TableText -->
满足真实成本、自愿性、方向和结构后果条件的人类行动

<!-- source-paragraph:V82-P4372 style=TableText -->
跨尺度保持项（scale_invariants）

<!-- source-paragraph:V82-P4373 style=TableText -->
1. 成本、自愿性、方向、替代解释、后果与停止权

<!-- source-paragraph:V82-P4374 style=TableText -->
升格必补项（required_scale_additions）

<!-- source-paragraph:V82-P4375 style=TableText -->
1. 自愿性分布

<!-- source-paragraph:V82-P4376 style=TableText -->
2. 代表关系

<!-- source-paragraph:V82-P4377 style=TableText -->
3. 成本外溢

<!-- source-paragraph:V82-P4378 style=TableText -->
4. 真实退出与代理保护

<!-- source-paragraph:V82-P4379 style=TableText -->
随尺度改变项（changing_semantics）

<!-- source-paragraph:V82-P4380 style=TableText -->
1. 承担形式、成本位置和受益对象可改变

<!-- source-paragraph:V82-P4381 style=TableText -->
不适用对象（non_applicable_objects）

<!-- source-paragraph:V82-P4382 style=TableText -->
1. 无意向、自愿性、责任或意义能力的非人系统

<!-- source-paragraph:V82-P4383 style=TableText -->
禁止升格（forbidden_elevation）

<!-- source-paragraph:V82-P4384 style=TableText -->
1. 个体承担升格为群体义务

<!-- source-paragraph:V82-P4385 style=TableText -->
2. 人类承担概念迁入非人核心

<!-- source-paragraph:V82-P4386 style=CardLabel -->
D. 状态、证据与变量流

<!-- source-paragraph:V82-P4387 style=TableHead -->
字段

<!-- source-paragraph:V82-P4388 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4389 style=TableText -->
状态集合（state）

<!-- source-paragraph:V82-P4390 style=TableText -->
1. 候选

<!-- source-paragraph:V82-P4391 style=TableText -->
2. 自愿且有限

<!-- source-paragraph:V82-P4392 style=TableText -->
3. 强制风险

<!-- source-paragraph:V82-P4393 style=TableText -->
4. 单方耗竭

<!-- source-paragraph:V82-P4394 style=TableText -->
5. 停止或退出

<!-- source-paragraph:V82-P4395 style=TableText -->
可观测项（observables）

<!-- source-paragraph:V82-P4396 style=TableText -->
1. 行动投入的时间、资源、机会与身体心理成本

<!-- source-paragraph:V82-P4397 style=TableText -->
2. 拒绝、退出、停止和重新协商是否真实可用

<!-- source-paragraph:V82-P4398 style=TableText -->
3. 行动方向、受益位置和可检测结构后果

<!-- source-paragraph:V82-P4399 style=TableText -->
4. 强制、恐惧、依赖、利益与表演等替代解释

<!-- source-paragraph:V82-P4400 style=TableText -->
证据要求（evidence）

<!-- source-paragraph:V82-P4401 style=TableText -->
1. 行动与成本

<!-- source-paragraph:V82-P4402 style=TableText -->
2. 拒绝和退出条件

<!-- source-paragraph:V82-P4403 style=TableText -->
3. 替代解释

<!-- source-paragraph:V82-P4404 style=TableText -->
4. 受益与后果

<!-- source-paragraph:V82-P4405 style=TableText -->
输入依赖与接口内容（input_dependencies）

<!-- source-paragraph:V82-P4406 style=TableText -->
1. 指向锚点

<!-- source-paragraph:V82-P4407 style=TableText -->
2. 承接层

<!-- source-paragraph:V82-P4408 style=TableText -->
3. 条件势场

<!-- source-paragraph:V82-P4409 style=TableText -->
4. 权力与安全

<!-- source-paragraph:V82-P4410 style=TableText -->
输出效应与变量流（output_effects）

<!-- source-paragraph:V82-P4411 style=TableText -->
1. 成本分布

<!-- source-paragraph:V82-P4412 style=TableText -->
2. 关系和制度状态

<!-- source-paragraph:V82-P4413 style=TableText -->
3. 停止与修复

<!-- source-paragraph:V82-P4414 style=TableText -->
时间窗与时滞（time_window_and_lag）

<!-- source-paragraph:V82-P4415 style=TableText -->
登记即时成本、持续承担、耗竭与恢复时滞

<!-- source-paragraph:V82-P4416 style=TableText -->
不确定性（uncertainty）

<!-- source-paragraph:V82-P4417 style=TableText -->
记录依赖、恐惧、隐性强制与表达安全

<!-- source-paragraph:V82-P4418 style=TableText -->
局部排除区（local_exclusion_zone）

<!-- source-paragraph:V82-P4419 style=TableText -->
无法安全拒绝、无法退出或被道德压力遮蔽的位置

<!-- source-paragraph:V82-P4420 style=TableText -->
受影响位置（affected_positions）

<!-- source-paragraph:V82-P4421 style=TableText -->
1. 行动者

<!-- source-paragraph:V82-P4422 style=TableText -->
2. 受益者

<!-- source-paragraph:V82-P4423 style=TableText -->
3. 依赖者

<!-- source-paragraph:V82-P4424 style=TableText -->
4. 替代承接者

<!-- source-paragraph:V82-P4425 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

<!-- source-paragraph:V82-P4426 style=TableHead -->
字段

<!-- source-paragraph:V82-P4427 style=TableHead -->
登记内容

<!-- source-paragraph:V82-P4428 style=TableText -->
承接载体（carrier）

<!-- source-paragraph:V82-P4429 style=TableText -->
1. 具体行动者

<!-- source-paragraph:V82-P4430 style=TableText -->
2. 关系实践

<!-- source-paragraph:V82-P4431 style=TableText -->
3. 照护或责任安排

<!-- source-paragraph:V82-P4432 style=TableText -->
责任主体（responsible_subject）

<!-- source-paragraph:V82-P4433 style=TableText -->
1. 提出要求者

<!-- source-paragraph:V82-P4434 style=TableText -->
2. 授权者

<!-- source-paragraph:V82-P4435 style=TableText -->
3. 受益责任者

<!-- source-paragraph:V82-P4436 style=TableText -->
4. 补救责任者

<!-- source-paragraph:V82-P4437 style=TableText -->
规范地位（normative_status）

<!-- source-paragraph:V82-P4438 style=TableText -->
受N4约束，不可命令或征用

<!-- source-paragraph:V82-P4439 style=TableText -->
判断上限（judgment_ceiling）

<!-- source-paragraph:V82-P4440 style=TableText -->
证据充分时只到行动描述级，不进入人格诊断

<!-- source-paragraph:V82-P4441 style=TableText -->
行动上限（action_ceiling）

<!-- source-paragraph:V82-P4442 style=TableText -->
本变量只生成自愿性、真实成本、方向、替代解释、结构后果与停止保护需求描述，不授权保护措施、承担要求、资源征用或人格裁决；任何现实调整须另过C12、运行时显式N前提、J授权与O程序

<!-- source-paragraph:V82-P4443 style=TableText -->
反例（counterexamples）

<!-- source-paragraph:V82-P4444 style=TableText -->
1. 无法拒绝的单方牺牲被赞美为爱或责任

<!-- source-paragraph:V82-P4445 style=TableText -->
2. 承担宣称没有真实成本、行动方向或可检测结构后果

<!-- source-paragraph:V82-P4446 style=TableText -->
申诉（appeal）

<!-- source-paragraph:V82-P4447 style=TableText -->
依appeal_and_rollback_rule，行动者可经安全可达、反报复通道拒绝被代表，说明强制、成本、替代解释和退出限制，并触发与原承担判断或要求链独立的复核

<!-- source-paragraph:V82-P4448 style=TableText -->
回滚（rollback）

<!-- source-paragraph:V82-P4449 style=TableText -->
依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销承担命名与相关要求，实际恢复拒绝、退出、记录和资源状态，保留版本与完成验证

<!-- source-paragraph:V82-P4450 style=BodyCJK -->
scale_profile 不是“微观—宏观”的单轴标签，而是 SP=<A,X,T,O,C,R,I,N,J> 的完整九轴记录：A 是聚合层次，必须声明单元、总体、分布和聚合规则；X 是物理空间与数字边界；T 是窗口、时滞和周期；O 是角色、团队、组织、制度与治理生态的组织层级；C 是事件、互动机制、中观结构、制度和系统条件的因果层次；R 是原始事件、序列、个案、分布、指标与摘要的观察分辨率，并记录压缩损失；I 是直接、间接、二阶、跨域与代际的受影响范围；N 是网络拓扑范围；J 是管辖与授权范围。扩大 A、X、O 或 I 不会自动扩大 J；观察更多不能产生更大处置权。

<!-- source-paragraph:V82-P4451 style=BodyCJK -->
身份与同一性判据属于对象合同 K，关系与作用通道进入 input_dependencies、carrier 或因果合同，成员与受影响位置进入 affected_positions、local_exclusion_zone 和观察字段；它们都不能冒充尺度轴。尺度轴 N 指网络拓扑；下文“运行时显式 N 前提”指规范选择层 N1-N5，两者不可混用。

<!-- source-paragraph:V82-P4452 style=BodyCJK -->
十一项变量共享同一行动边界：变量本身只生成描述、证据缺口与行动需求，不授权现实调整。其输出上限如下。

<!-- source-paragraph:V82-P4453 style=TableHead -->
变量

<!-- source-paragraph:V82-P4454 style=TableHead -->
本变量可生成的描述或需求

<!-- source-paragraph:V82-P4455 style=TableText -->
HV01

<!-- source-paragraph:V82-P4456 style=TableText -->
候选结构域、边界争议与补证需求

<!-- source-paragraph:V82-P4457 style=TableText -->
HV02

<!-- source-paragraph:V82-P4458 style=TableText -->
边界状态、接口障碍、排除风险与测试需求

<!-- source-paragraph:V82-P4459 style=TableText -->
HV03

<!-- source-paragraph:V82-P4460 style=TableText -->
候选锚点、异质表达、比较结果与补证需求

<!-- source-paragraph:V82-P4461 style=TableText -->
HV04

<!-- source-paragraph:V82-P4462 style=TableText -->
GC、GS、GE 候选分型、状态转移与补证需求

<!-- source-paragraph:V82-P4463 style=TableText -->
HV05

<!-- source-paragraph:V82-P4464 style=TableText -->
CV、RS、成本、容量、停止权、承接缺口及减载、补资源或重分配需求

<!-- source-paragraph:V82-P4465 style=TableText -->
HV06

<!-- source-paragraph:V82-P4466 style=TableText -->
链条连通、时滞、损耗、中断、成本与承接需求

<!-- source-paragraph:V82-P4467 style=TableText -->
HV07

<!-- source-paragraph:V82-P4468 style=TableText -->
受理、字段变化、执行、持续时间、写回缺口与程序修复需求

<!-- source-paragraph:V82-P4469 style=TableText -->
HV08

<!-- source-paragraph:V82-P4470 style=TableText -->
候选条件通道、位置异质性、证据遮蔽与风险降低需求

<!-- source-paragraph:V82-P4471 style=TableText -->
HV09

<!-- source-paragraph:V82-P4472 style=TableText -->
负荷、容量、恢复、局部过载与减载补资源需求

<!-- source-paragraph:V82-P4473 style=TableText -->
HV10

<!-- source-paragraph:V82-P4474 style=TableText -->
相位原型匹配、混合状态、不确定性与观察需求

<!-- source-paragraph:V82-P4475 style=TableText -->
HV11

<!-- source-paragraph:V82-P4476 style=TableText -->
自愿性、真实成本、方向、替代解释、结构后果与停止保护需求

<!-- source-paragraph:V82-P4477 style=BodyCJK -->
无论需求看起来多么明显，任何现实调整都须另过 C12、运行时显式 N 前提、J 授权与 O 程序。变量不得自行授权测试、减载、补资源、修复、保护、归责、试探、推进、退出安排或处置。

## Canonical Records

<!-- canonical-records:start -->
```json
{
  "paragraphs": [
    {
      "anchor": "V82-P2906",
      "ordinal": 2906,
      "style": "PartTitle",
      "text": "附录A　人类变量接口卡册"
    },
    {
      "anchor": "V82-P2907",
      "ordinal": 2907,
      "style": "BodyCJK",
      "text": "本附录完整收录第七部分十一项人类变量(HV01-HV11)的接口卡。每张卡按 A-E 五区登记:A 身份、命题与适用范围;B 正式依赖与推论边界;C 九轴尺度与对象合同;D 状态、证据与变量流;E 承接、责任、规范、上限与纠错。卡片内容与 v8.0 逐字一致,仅调整了表格版式与单元格内分行。"
    },
    {
      "anchor": "V82-P2908",
      "ordinal": 2908,
      "style": "BodyCJK",
      "text": "以下 11 张卡片逐项展开每个变量的全部 39 个正式字段，并与合同 JSON 逐值同步。依赖项的空集合明确写作“无（空集合）”；它只表示该类依赖没有登记对象，不表示证据充分或经验成立。条件支持路由必须逐条整体读取，不能把不同路由的有利条件事后并取。"
    },
    {
      "anchor": "V82-P2909",
      "ordinal": 2909,
      "style": "SecH2",
      "text": "A.1　HV01 结构域（完整接口卡）"
    },
    {
      "anchor": "V82-P2910",
      "ordinal": 2910,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P2911",
      "ordinal": 2911,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P2912",
      "ordinal": 2912,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P2913",
      "ordinal": 2913,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P2914",
      "ordinal": 2914,
      "style": "TableText",
      "text": "HV01"
    },
    {
      "anchor": "V82-P2915",
      "ordinal": 2915,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P2916",
      "ordinal": 2916,
      "style": "TableText",
      "text": "human_variable:HV01"
    },
    {
      "anchor": "V82-P2917",
      "ordinal": 2917,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P2918",
      "ordinal": 2918,
      "style": "TableText",
      "text": "结构域"
    },
    {
      "anchor": "V82-P2919",
      "ordinal": 2919,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P2920",
      "ordinal": 2920,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P2921",
      "ordinal": 2921,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P2922",
      "ordinal": 2922,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P2923",
      "ordinal": 2923,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P2924",
      "ordinal": 2924,
      "style": "TableText",
      "text": "D0只声明候选人类对象；只有预注册G1-instance显示候选分组相对匹配N0在预选结果上取得超过阈值的样本外或外推增益时，才在该实例范围登记有限有效结构域。"
    },
    {
      "anchor": "V82-P2925",
      "ordinal": 2925,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P2926",
      "ordinal": 2926,
      "style": "TableText",
      "text": "关系、团队、组织、制度与公共议题"
    },
    {
      "anchor": "V82-P2927",
      "ordinal": 2927,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P2928",
      "ordinal": 2928,
      "style": "TableText",
      "text": "对象、边界、尺度、时间窗、同一性或零模型不完整"
    },
    {
      "anchor": "V82-P2929",
      "ordinal": 2929,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P2930",
      "ordinal": 2930,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P2931",
      "ordinal": 2931,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P2932",
      "ordinal": 2932,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P2933",
      "ordinal": 2933,
      "style": "TableText",
      "text": "1. D0"
    },
    {
      "anchor": "V82-P2934",
      "ordinal": 2934,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P2935",
      "ordinal": 2935,
      "style": "TableText",
      "text": "1. E1"
    },
    {
      "anchor": "V82-P2936",
      "ordinal": 2936,
      "style": "TableText",
      "text": "2. EVIDENCE"
    },
    {
      "anchor": "V82-P2937",
      "ordinal": 2937,
      "style": "TableText",
      "text": "3. SOURCE"
    },
    {
      "anchor": "V82-P2938",
      "ordinal": 2938,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P2939",
      "ordinal": 2939,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P2940",
      "ordinal": 2940,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P2941",
      "ordinal": 2941,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P2942",
      "ordinal": 2942,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P2943",
      "ordinal": 2943,
      "style": "TableText",
      "text": "1. route_id=HV01-R0-candidate-object；"
    },
    {
      "anchor": "V82-P2944",
      "ordinal": 2944,
      "style": "TableText",
      "text": "claim_level=candidate_description；"
    },
    {
      "anchor": "V82-P2945",
      "ordinal": 2945,
      "style": "TableText",
      "text": "when=D0对象合同完整，但尚无符合资格且result_state=supported的G1-instance。；"
    },
    {
      "anchor": "V82-P2946",
      "ordinal": 2946,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P2947",
      "ordinal": 2947,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P2948",
      "ordinal": 2948,
      "style": "TableText",
      "text": "allowed_conclusion=登记候选人类对象、材料集合、边界争议与G1补证需求。；"
    },
    {
      "anchor": "V82-P2949",
      "ordinal": 2949,
      "style": "TableText",
      "text": "result_ceiling=仅到候选对象描述；不得称有限有效结构域，也不得限定HV02-HV11的经验对象范围。"
    },
    {
      "anchor": "V82-P2950",
      "ordinal": 2950,
      "style": "TableText",
      "text": "2. route_id=HV01-R1-effective-domain；"
    },
    {
      "anchor": "V82-P2951",
      "ordinal": 2951,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P2952",
      "ordinal": 2952,
      "style": "TableText",
      "text": "when=同一对象、尺度、窗口、K与外推单元内的预注册G1-instance取得supported。；"
    },
    {
      "anchor": "V82-P2953",
      "ordinal": 2953,
      "style": "TableText",
      "text": "additional_inferential_requires=G1-instance；"
    },
    {
      "anchor": "V82-P2954",
      "ordinal": 2954,
      "style": "TableText",
      "text": "additional_protocol_requires=E4；"
    },
    {
      "anchor": "V82-P2955",
      "ordinal": 2955,
      "style": "TableText",
      "text": "allowed_conclusion=登记该实例范围内的有限有效结构域、对象识别强度、边界可信度和适用窗。；"
    },
    {
      "anchor": "V82-P2956",
      "ordinal": 2956,
      "style": "TableText",
      "text": "result_ceiling=只限预注册SP/T/K与generalization_unit；不得作终极本体、统一意志或授权判断。"
    },
    {
      "anchor": "V82-P2957",
      "ordinal": 2957,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P2958",
      "ordinal": 2958,
      "style": "TableText",
      "text": "1. 只在G1-instance预注册对象、尺度、窗口、结果与外推单位内登记有限有效结构域及识别强度"
    },
    {
      "anchor": "V82-P2959",
      "ordinal": 2959,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P2960",
      "ordinal": 2960,
      "style": "TableText",
      "text": "1. 命名即客观共同体2. 共同处境即共同意愿"
    },
    {
      "anchor": "V82-P2961",
      "ordinal": 2961,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P2962",
      "ordinal": 2962,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P2963",
      "ordinal": 2963,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P2964",
      "ordinal": 2964,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P2965",
      "ordinal": 2965,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：关系或事件单元、候选成员总体、边界内外分布及分组规则；X=空间范围：共同场所、组织边界、数字平台与跨域外部环境；T=时间跨度：识别窗口、成员变动周期与边界历史；O=组织层级：角色、团队、组织、制度至治理生态；C=因果层次：原始事件、互动机制、中观关系结构、制度与系统条件；R=观察分辨率：原始互动、事件序列、成员个案、边界分布、指标与摘要，并登记压缩损失；I=影响范围：直接成员、被排除者、间接受影响者、二阶外溢、跨域与代际位置；N=网络拓扑范围：成员关系、边界连接、孤立点与跨域桥接；J=管辖与授权范围：对象命名、边界采用及后续处置分别登记授权；不适用轴须登记not_applicable理由"
    },
    {
      "anchor": "V82-P2966",
      "ordinal": 2966,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P2967",
      "ordinal": 2967,
      "style": "TableText",
      "text": "由D0声明的候选对象；只有通过预注册G1-instance相对匹配N0的阈值检验后，才在该实例范围登记为有限有效结构域"
    },
    {
      "anchor": "V82-P2968",
      "ordinal": 2968,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P2969",
      "ordinal": 2969,
      "style": "TableText",
      "text": "1. 对象合同2. 参与与受影响位置"
    },
    {
      "anchor": "V82-P2970",
      "ordinal": 2970,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P2971",
      "ordinal": 2971,
      "style": "TableText",
      "text": "1. 单位与总体"
    },
    {
      "anchor": "V82-P2972",
      "ordinal": 2972,
      "style": "TableText",
      "text": "2. 代表性"
    },
    {
      "anchor": "V82-P2973",
      "ordinal": 2973,
      "style": "TableText",
      "text": "3. J轴"
    },
    {
      "anchor": "V82-P2974",
      "ordinal": 2974,
      "style": "TableText",
      "text": "4. 低可见位置"
    },
    {
      "anchor": "V82-P2975",
      "ordinal": 2975,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P2976",
      "ordinal": 2976,
      "style": "TableText",
      "text": "1. 有效成员、关系和同一性可随尺度改变"
    },
    {
      "anchor": "V82-P2977",
      "ordinal": 2977,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P2978",
      "ordinal": 2978,
      "style": "TableText",
      "text": "1. 无意向、制度或责任接口的非人系统"
    },
    {
      "anchor": "V82-P2979",
      "ordinal": 2979,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P2980",
      "ordinal": 2980,
      "style": "TableText",
      "text": "1. 局部群体直接代表全部受影响者"
    },
    {
      "anchor": "V82-P2981",
      "ordinal": 2981,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P2982",
      "ordinal": 2982,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P2983",
      "ordinal": 2983,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P2984",
      "ordinal": 2984,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P2985",
      "ordinal": 2985,
      "style": "TableText",
      "text": "1. 候选2. 可识别3. 边界争议4. 不成立"
    },
    {
      "anchor": "V82-P2986",
      "ordinal": 2986,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P2987",
      "ordinal": 2987,
      "style": "TableText",
      "text": "1. 边界内外关系密度与约束差异"
    },
    {
      "anchor": "V82-P2988",
      "ordinal": 2988,
      "style": "TableText",
      "text": "2. 成员进入、退出与被排除记录"
    },
    {
      "anchor": "V82-P2989",
      "ordinal": 2989,
      "style": "TableText",
      "text": "3. 共同问题、资源通道或制度规则的重复共现"
    },
    {
      "anchor": "V82-P2990",
      "ordinal": 2990,
      "style": "TableText",
      "text": "4. 改变分组规则后对象识别是否稳定"
    },
    {
      "anchor": "V82-P2991",
      "ordinal": 2991,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P2992",
      "ordinal": 2992,
      "style": "TableText",
      "text": "1. D0候选对象与同一性记录"
    },
    {
      "anchor": "V82-P2993",
      "ordinal": 2993,
      "style": "TableText",
      "text": "2. G1-instance预注册表及匹配N0"
    },
    {
      "anchor": "V82-P2994",
      "ordinal": 2994,
      "style": "TableText",
      "text": "3. 训练与样本外或外推结果"
    },
    {
      "anchor": "V82-P2995",
      "ordinal": 2995,
      "style": "TableText",
      "text": "4. 候选分组与竞争分组的增益比较"
    },
    {
      "anchor": "V82-P2996",
      "ordinal": 2996,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P2997",
      "ordinal": 2997,
      "style": "TableText",
      "text": "1. D0只提供候选对象字段，不构成结构成立证据"
    },
    {
      "anchor": "V82-P2998",
      "ordinal": 2998,
      "style": "TableText",
      "text": "2. 预注册G1-instance及匹配N0、阈值、模型类、样本或外推单位"
    },
    {
      "anchor": "V82-P2999",
      "ordinal": 2999,
      "style": "TableText",
      "text": "3. 观察位置、竞争分组与E1协议"
    },
    {
      "anchor": "V82-P3000",
      "ordinal": 3000,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3001",
      "ordinal": 3001,
      "style": "TableText",
      "text": "1. 仅在G1-instance通过后限定其余十变量的对象范围；未通过时保持候选或材料集合"
    },
    {
      "anchor": "V82-P3002",
      "ordinal": 3002,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3003",
      "ordinal": 3003,
      "style": "TableText",
      "text": "登记识别窗口、边界变动与成员变化时滞"
    },
    {
      "anchor": "V82-P3004",
      "ordinal": 3004,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3005",
      "ordinal": 3005,
      "style": "TableText",
      "text": "记录边界争议、成员缺席和观察覆盖"
    },
    {
      "anchor": "V82-P3006",
      "ordinal": 3006,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3007",
      "ordinal": 3007,
      "style": "TableText",
      "text": "无法安全表达或未被采样的位置不得被总体代表"
    },
    {
      "anchor": "V82-P3008",
      "ordinal": 3008,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3009",
      "ordinal": 3009,
      "style": "TableText",
      "text": "1. 成员2. 被排除者3. 边界外成本承担者"
    },
    {
      "anchor": "V82-P3010",
      "ordinal": 3010,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3011",
      "ordinal": 3011,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3012",
      "ordinal": 3012,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3013",
      "ordinal": 3013,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3014",
      "ordinal": 3014,
      "style": "TableText",
      "text": "1. 关系网络2. 组织边界3. 制度记录"
    },
    {
      "anchor": "V82-P3015",
      "ordinal": 3015,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3016",
      "ordinal": 3016,
      "style": "TableText",
      "text": "1. 提出结构域判断的分析者"
    },
    {
      "anchor": "V82-P3017",
      "ordinal": 3017,
      "style": "TableText",
      "text": "2. 使用该判断的决策者"
    },
    {
      "anchor": "V82-P3018",
      "ordinal": 3018,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3019",
      "ordinal": 3019,
      "style": "TableText",
      "text": "描述性H-World接口，不产生正当性"
    },
    {
      "anchor": "V82-P3020",
      "ordinal": 3020,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3021",
      "ordinal": 3021,
      "style": "TableText",
      "text": "只有G1-instance通过时，且仅限预注册对象、尺度、窗口、结果与外推单位，才可登记解释级有限有效对象；否则仅为候选对象或材料集合"
    },
    {
      "anchor": "V82-P3022",
      "ordinal": 3022,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3023",
      "ordinal": 3023,
      "style": "TableText",
      "text": "本变量只生成候选结构域、边界争议与补证需求描述，不授权纳入、排除或处置；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3024",
      "ordinal": 3024,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3025",
      "ordinal": 3025,
      "style": "TableText",
      "text": "1. 同一场所中反复共现的人群没有稳定关系或共同约束"
    },
    {
      "anchor": "V82-P3026",
      "ordinal": 3026,
      "style": "TableText",
      "text": "2. 分析者划定的群组在改变分组规则后立即消失"
    },
    {
      "anchor": "V82-P3027",
      "ordinal": 3027,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3028",
      "ordinal": 3028,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，成员与受影响位置可经安全可达、反报复通道挑战边界、代表性和同一性判据，并触发与原命名或决策链独立的复核"
    },
    {
      "anchor": "V82-P3029",
      "ordinal": 3029,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3030",
      "ordinal": 3030,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销结构域登记、移除其对下游对象范围的效力并恢复为材料集合，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3031",
      "ordinal": 3031,
      "style": "SecH2",
      "text": "A.2　HV02 边界与接口（完整接口卡）"
    },
    {
      "anchor": "V82-P3032",
      "ordinal": 3032,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3033",
      "ordinal": 3033,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3034",
      "ordinal": 3034,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3035",
      "ordinal": 3035,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3036",
      "ordinal": 3036,
      "style": "TableText",
      "text": "HV02"
    },
    {
      "anchor": "V82-P3037",
      "ordinal": 3037,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3038",
      "ordinal": 3038,
      "style": "TableText",
      "text": "human_variable:HV02"
    },
    {
      "anchor": "V82-P3039",
      "ordinal": 3039,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3040",
      "ordinal": 3040,
      "style": "TableText",
      "text": "边界与接口"
    },
    {
      "anchor": "V82-P3041",
      "ordinal": 3041,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3042",
      "ordinal": 3042,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3043",
      "ordinal": 3043,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3044",
      "ordinal": 3044,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3045",
      "ordinal": 3045,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3046",
      "ordinal": 3046,
      "style": "TableText",
      "text": "人类边界必须同时登记成员、资源、信息、权利、责任与跨界接口。"
    },
    {
      "anchor": "V82-P3047",
      "ordinal": 3047,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3048",
      "ordinal": 3048,
      "style": "TableText",
      "text": "存在纳入、排除、交换或管辖的人类结构"
    },
    {
      "anchor": "V82-P3049",
      "ordinal": 3049,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3050",
      "ordinal": 3050,
      "style": "TableText",
      "text": "正式边界与实际边界混同或排除项不可见"
    },
    {
      "anchor": "V82-P3051",
      "ordinal": 3051,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3052",
      "ordinal": 3052,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3053",
      "ordinal": 3053,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3054",
      "ordinal": 3054,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3055",
      "ordinal": 3055,
      "style": "TableText",
      "text": "1. human_variable:HV01"
    },
    {
      "anchor": "V82-P3056",
      "ordinal": 3056,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3057",
      "ordinal": 3057,
      "style": "TableText",
      "text": "1. E1"
    },
    {
      "anchor": "V82-P3058",
      "ordinal": 3058,
      "style": "TableText",
      "text": "2. EVIDENCE"
    },
    {
      "anchor": "V82-P3059",
      "ordinal": 3059,
      "style": "TableText",
      "text": "3. SOURCE"
    },
    {
      "anchor": "V82-P3060",
      "ordinal": 3060,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3061",
      "ordinal": 3061,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3062",
      "ordinal": 3062,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3063",
      "ordinal": 3063,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3064",
      "ordinal": 3064,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3065",
      "ordinal": 3065,
      "style": "TableText",
      "text": "1. route_id=HV02-R0-boundary-inventory；"
    },
    {
      "anchor": "V82-P3066",
      "ordinal": 3066,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3067",
      "ordinal": 3067,
      "style": "TableText",
      "text": "when=成员、资源、信息、权利、责任、跨界接口及正式—实际边界差异可逐项登记。；"
    },
    {
      "anchor": "V82-P3068",
      "ordinal": 3068,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3069",
      "ordinal": 3069,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3070",
      "ordinal": 3070,
      "style": "TableText",
      "text": "allowed_conclusion=描述边界状态、接口通达性、守门位置、拒绝记录与排除风险。；"
    },
    {
      "anchor": "V82-P3071",
      "ordinal": 3071,
      "style": "TableText",
      "text": "result_ceiling=只到边界与接口清单；不得断言边界已产生因果选择效应。"
    },
    {
      "anchor": "V82-P3072",
      "ordinal": 3072,
      "style": "TableText",
      "text": "2. route_id=HV02-R1-selective-effect；"
    },
    {
      "anchor": "V82-P3073",
      "ordinal": 3073,
      "style": "TableText",
      "text": "claim_level=conditional_effect；"
    },
    {
      "anchor": "V82-P3074",
      "ordinal": 3074,
      "style": "TableText",
      "text": "when=预注册边界或接口变动经符合资格的G2-instance显示对指定跨界流、准入或拒绝结果有超过阈值的通道效应。；"
    },
    {
      "anchor": "V82-P3075",
      "ordinal": 3075,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance；"
    },
    {
      "anchor": "V82-P3076",
      "ordinal": 3076,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3077",
      "ordinal": 3077,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定通道、窗口与位置上的边界选择效应及跨界成本分布。；"
    },
    {
      "anchor": "V82-P3078",
      "ordinal": 3078,
      "style": "TableText",
      "text": "result_ceiling=只限已检验通道与结果；不得从空间、组织或影响范围推出J轴管辖与处置权。"
    },
    {
      "anchor": "V82-P3079",
      "ordinal": 3079,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3080",
      "ordinal": 3080,
      "style": "TableText",
      "text": "1. 边界选择性2. 接口通达性3. 跨界成本"
    },
    {
      "anchor": "V82-P3081",
      "ordinal": 3081,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3082",
      "ordinal": 3082,
      "style": "TableText",
      "text": "1. 边界等于封闭"
    },
    {
      "anchor": "V82-P3083",
      "ordinal": 3083,
      "style": "TableText",
      "text": "2. 成员身份等于同意"
    },
    {
      "anchor": "V82-P3084",
      "ordinal": 3084,
      "style": "TableText",
      "text": "3. 影响范围等于管辖权"
    },
    {
      "anchor": "V82-P3085",
      "ordinal": 3085,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3086",
      "ordinal": 3086,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3087",
      "ordinal": 3087,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3088",
      "ordinal": 3088,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3089",
      "ordinal": 3089,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次跨界事件、接口使用个案、成员类别总体、准入拒绝分布及聚合规则；X=空间范围：物理入口、组织边界、数字接口、司法辖区与跨域通道；T=时间跨度：边界生效期、接口等待、迁移时滞与重组周期；O=组织层级：使用者角色、守门团队、组织、制度至治理生态；C=因果层次：跨界事件、守门互动机制、接口结构、制度规则与系统条件；R=观察分辨率：原始准入拒绝记录、使用序列、个案、流量分布、服务指标与摘要，并登记压缩损失；I=影响范围：直接使用者、被排除者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：接口节点、守门瓶颈、替代路径与跨域连接；J=管辖与授权范围：纳入、排除、接口改变及权利责任调整分别登记授权；升格须记录逐轴差值"
    },
    {
      "anchor": "V82-P3090",
      "ordinal": 3090,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3091",
      "ordinal": 3091,
      "style": "TableText",
      "text": "对资源、信息、权利或责任流产生选择性的边界"
    },
    {
      "anchor": "V82-P3092",
      "ordinal": 3092,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3093",
      "ordinal": 3093,
      "style": "TableText",
      "text": "1. 内外位置2. 跨界通道3. 权利责任边界"
    },
    {
      "anchor": "V82-P3094",
      "ordinal": 3094,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3095",
      "ordinal": 3095,
      "style": "TableText",
      "text": "1. 新成员类别"
    },
    {
      "anchor": "V82-P3096",
      "ordinal": 3096,
      "style": "TableText",
      "text": "2. 跨域接口"
    },
    {
      "anchor": "V82-P3097",
      "ordinal": 3097,
      "style": "TableText",
      "text": "3. 代表与授权"
    },
    {
      "anchor": "V82-P3098",
      "ordinal": 3098,
      "style": "TableText",
      "text": "4. 保护继承"
    },
    {
      "anchor": "V82-P3099",
      "ordinal": 3099,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3100",
      "ordinal": 3100,
      "style": "TableText",
      "text": "1. 成员、接口与实际控制边界可改变"
    },
    {
      "anchor": "V82-P3101",
      "ordinal": 3101,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3102",
      "ordinal": 3102,
      "style": "TableText",
      "text": "1. 无成员、权利或责任概念的非人边界"
    },
    {
      "anchor": "V82-P3103",
      "ordinal": 3103,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3104",
      "ordinal": 3104,
      "style": "TableText",
      "text": "1. 空间或组织范围扩大自动产生管辖权"
    },
    {
      "anchor": "V82-P3105",
      "ordinal": 3105,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3106",
      "ordinal": 3106,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3107",
      "ordinal": 3107,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3108",
      "ordinal": 3108,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3109",
      "ordinal": 3109,
      "style": "TableText",
      "text": "1. 开放"
    },
    {
      "anchor": "V82-P3110",
      "ordinal": 3110,
      "style": "TableText",
      "text": "2. 选择性开放"
    },
    {
      "anchor": "V82-P3111",
      "ordinal": 3111,
      "style": "TableText",
      "text": "3. 封闭"
    },
    {
      "anchor": "V82-P3112",
      "ordinal": 3112,
      "style": "TableText",
      "text": "4. 争议"
    },
    {
      "anchor": "V82-P3113",
      "ordinal": 3113,
      "style": "TableText",
      "text": "5. 重组"
    },
    {
      "anchor": "V82-P3114",
      "ordinal": 3114,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3115",
      "ordinal": 3115,
      "style": "TableText",
      "text": "1. 成员资格、准入与退出决定"
    },
    {
      "anchor": "V82-P3116",
      "ordinal": 3116,
      "style": "TableText",
      "text": "2. 资源、信息、权利和责任的跨界流量"
    },
    {
      "anchor": "V82-P3117",
      "ordinal": 3117,
      "style": "TableText",
      "text": "3. 守门节点、等待时间与拒绝理由"
    },
    {
      "anchor": "V82-P3118",
      "ordinal": 3118,
      "style": "TableText",
      "text": "4. 正式边界与实际通行边界的差异"
    },
    {
      "anchor": "V82-P3119",
      "ordinal": 3119,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3120",
      "ordinal": 3120,
      "style": "TableText",
      "text": "1. 成员名单与例外"
    },
    {
      "anchor": "V82-P3121",
      "ordinal": 3121,
      "style": "TableText",
      "text": "2. 接口使用记录"
    },
    {
      "anchor": "V82-P3122",
      "ordinal": 3122,
      "style": "TableText",
      "text": "3. 跨界流和拒绝记录"
    },
    {
      "anchor": "V82-P3123",
      "ordinal": 3123,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3124",
      "ordinal": 3124,
      "style": "TableText",
      "text": "1. HV01结构域2. 角色与授权"
    },
    {
      "anchor": "V82-P3125",
      "ordinal": 3125,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3126",
      "ordinal": 3126,
      "style": "TableText",
      "text": "1. HV05承接"
    },
    {
      "anchor": "V82-P3127",
      "ordinal": 3127,
      "style": "TableText",
      "text": "2. HV07写回"
    },
    {
      "anchor": "V82-P3128",
      "ordinal": 3128,
      "style": "TableText",
      "text": "3. PF-9退出"
    },
    {
      "anchor": "V82-P3129",
      "ordinal": 3129,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3130",
      "ordinal": 3130,
      "style": "TableText",
      "text": "记录边界生效、变更、退出和申诉时滞"
    },
    {
      "anchor": "V82-P3131",
      "ordinal": 3131,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3132",
      "ordinal": 3132,
      "style": "TableText",
      "text": "记录非正式边界、代理访问和数字空间漂移"
    },
    {
      "anchor": "V82-P3133",
      "ordinal": 3133,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3134",
      "ordinal": 3134,
      "style": "TableText",
      "text": "无法接入接口、无法退出或受保护不公开的位置"
    },
    {
      "anchor": "V82-P3135",
      "ordinal": 3135,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3136",
      "ordinal": 3136,
      "style": "TableText",
      "text": "1. 成员"
    },
    {
      "anchor": "V82-P3137",
      "ordinal": 3137,
      "style": "TableText",
      "text": "2. 申请者"
    },
    {
      "anchor": "V82-P3138",
      "ordinal": 3138,
      "style": "TableText",
      "text": "3. 被排除者"
    },
    {
      "anchor": "V82-P3139",
      "ordinal": 3139,
      "style": "TableText",
      "text": "4. 边界外承担者"
    },
    {
      "anchor": "V82-P3140",
      "ordinal": 3140,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3141",
      "ordinal": 3141,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3142",
      "ordinal": 3142,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3143",
      "ordinal": 3143,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3144",
      "ordinal": 3144,
      "style": "TableText",
      "text": "1. 成员规则"
    },
    {
      "anchor": "V82-P3145",
      "ordinal": 3145,
      "style": "TableText",
      "text": "2. 访问机制"
    },
    {
      "anchor": "V82-P3146",
      "ordinal": 3146,
      "style": "TableText",
      "text": "3. 法律或制度边界"
    },
    {
      "anchor": "V82-P3147",
      "ordinal": 3147,
      "style": "TableText",
      "text": "4. 技术接口"
    },
    {
      "anchor": "V82-P3148",
      "ordinal": 3148,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3149",
      "ordinal": 3149,
      "style": "TableText",
      "text": "1. 边界制定者2. 接口运营者3. 授权者"
    },
    {
      "anchor": "V82-P3150",
      "ordinal": 3150,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3151",
      "ordinal": 3151,
      "style": "TableText",
      "text": "边界事实与边界正当性分离"
    },
    {
      "anchor": "V82-P3152",
      "ordinal": 3152,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3153",
      "ordinal": 3153,
      "style": "TableText",
      "text": "接口与影响证据充分时至诊断级"
    },
    {
      "anchor": "V82-P3154",
      "ordinal": 3154,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3155",
      "ordinal": 3155,
      "style": "TableText",
      "text": "本变量只生成边界状态、接口障碍、排除风险与测试需求描述，不授权改变准入、退出、权利或资源流；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3156",
      "ordinal": 3156,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3157",
      "ordinal": 3157,
      "style": "TableText",
      "text": "1. 正式成员边界与实际资源控制边界相反"
    },
    {
      "anchor": "V82-P3158",
      "ordinal": 3158,
      "style": "TableText",
      "text": "2. 数字接口开放但物理、语言或安全门槛使部分位置无法进入"
    },
    {
      "anchor": "V82-P3159",
      "ordinal": 3159,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3160",
      "ordinal": 3160,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，边界内外受影响者可经安全可达、反报复通道挑战纳入、排除和接口障碍，并触发与原边界决策链独立的复核"
    },
    {
      "anchor": "V82-P3161",
      "ordinal": 3161,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3162",
      "ordinal": 3162,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正成员与拒绝记录、实际恢复受影响的准入权利或接口状态并撤销错误边界行动，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3163",
      "ordinal": 3163,
      "style": "SecH2",
      "text": "A.3　HV03 指向锚点（完整接口卡）"
    },
    {
      "anchor": "V82-P3164",
      "ordinal": 3164,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3165",
      "ordinal": 3165,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3166",
      "ordinal": 3166,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3167",
      "ordinal": 3167,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3168",
      "ordinal": 3168,
      "style": "TableText",
      "text": "HV03"
    },
    {
      "anchor": "V82-P3169",
      "ordinal": 3169,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3170",
      "ordinal": 3170,
      "style": "TableText",
      "text": "human_variable:HV03"
    },
    {
      "anchor": "V82-P3171",
      "ordinal": 3171,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3172",
      "ordinal": 3172,
      "style": "TableText",
      "text": "指向锚点"
    },
    {
      "anchor": "V82-P3173",
      "ordinal": 3173,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3174",
      "ordinal": 3174,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3175",
      "ordinal": 3175,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3176",
      "ordinal": 3176,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3177",
      "ordinal": 3177,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3178",
      "ordinal": 3178,
      "style": "TableText",
      "text": "目标、身份、记忆、承诺、恐惧或共同问题只有改变资源与行动时才构成指向锚点。"
    },
    {
      "anchor": "V82-P3179",
      "ordinal": 3179,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3180",
      "ordinal": 3180,
      "style": "TableText",
      "text": "具有意向、协调或共同问题的人类结构"
    },
    {
      "anchor": "V82-P3181",
      "ordinal": 3181,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3182",
      "ordinal": 3182,
      "style": "TableText",
      "text": "只有口号、解释者投射或被强制的一致表达"
    },
    {
      "anchor": "V82-P3183",
      "ordinal": 3183,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3184",
      "ordinal": 3184,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3185",
      "ordinal": 3185,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3186",
      "ordinal": 3186,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3187",
      "ordinal": 3187,
      "style": "TableText",
      "text": "1. human_variable:HV01"
    },
    {
      "anchor": "V82-P3188",
      "ordinal": 3188,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3189",
      "ordinal": 3189,
      "style": "TableText",
      "text": "1. E2"
    },
    {
      "anchor": "V82-P3190",
      "ordinal": 3190,
      "style": "TableText",
      "text": "2. EVIDENCE"
    },
    {
      "anchor": "V82-P3191",
      "ordinal": 3191,
      "style": "TableText",
      "text": "3. SOURCE"
    },
    {
      "anchor": "V82-P3192",
      "ordinal": 3192,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3193",
      "ordinal": 3193,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3194",
      "ordinal": 3194,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3195",
      "ordinal": 3195,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3196",
      "ordinal": 3196,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3197",
      "ordinal": 3197,
      "style": "TableText",
      "text": "1. route_id=HV03-R0-candidate-anchor；"
    },
    {
      "anchor": "V82-P3198",
      "ordinal": 3198,
      "style": "TableText",
      "text": "claim_level=candidate_description；"
    },
    {
      "anchor": "V82-P3199",
      "ordinal": 3199,
      "style": "TableText",
      "text": "when=目标、身份、记忆、承诺、恐惧或共同问题有可追踪表达与承载形式，但尚无符合资格的H1-instance。；"
    },
    {
      "anchor": "V82-P3200",
      "ordinal": 3200,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3201",
      "ordinal": 3201,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3202",
      "ordinal": 3202,
      "style": "TableText",
      "text": "allowed_conclusion=登记候选意义材料、异质表达、代表性争议与H1补证需求。；"
    },
    {
      "anchor": "V82-P3203",
      "ordinal": 3203,
      "style": "TableText",
      "text": "result_ceiling=仅称候选意义表达；不得称有效指向锚点或共同意志。"
    },
    {
      "anchor": "V82-P3204",
      "ordinal": 3204,
      "style": "TableText",
      "text": "2. route_id=HV03-R1-effective-anchor；"
    },
    {
      "anchor": "V82-P3205",
      "ordinal": 3205,
      "style": "TableText",
      "text": "claim_level=conditional_effect；"
    },
    {
      "anchor": "V82-P3206",
      "ordinal": 3206,
      "style": "TableText",
      "text": "when=预注册H1-instance在资源配置、行动选择或协调结果中唯一预选的判据取得supported。；"
    },
    {
      "anchor": "V82-P3207",
      "ordinal": 3207,
      "style": "TableText",
      "text": "additional_inferential_requires=H1-instance；"
    },
    {
      "anchor": "V82-P3208",
      "ordinal": 3208,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3209",
      "ordinal": 3209,
      "style": "TableText",
      "text": "allowed_conclusion=登记该实例、结果家族、尺度与窗口内的条件性有效指向锚点。；"
    },
    {
      "anchor": "V82-P3210",
      "ordinal": 3210,
      "style": "TableText",
      "text": "result_ceiling=不外推到未选资源、行动或协调结果，也不推出真实同意、统一内心或强制统一意义。"
    },
    {
      "anchor": "V82-P3211",
      "ordinal": 3211,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3212",
      "ordinal": 3212,
      "style": "TableText",
      "text": "1. 条件性的协调方向与冲突锚点"
    },
    {
      "anchor": "V82-P3213",
      "ordinal": 3213,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3214",
      "ordinal": 3214,
      "style": "TableText",
      "text": "1. 群体具有统一内心"
    },
    {
      "anchor": "V82-P3215",
      "ordinal": 3215,
      "style": "TableText",
      "text": "2. 共同语言等于真实同意"
    },
    {
      "anchor": "V82-P3216",
      "ordinal": 3216,
      "style": "TableText",
      "text": "3. 目标正当"
    },
    {
      "anchor": "V82-P3217",
      "ordinal": 3217,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3218",
      "ordinal": 3218,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3219",
      "ordinal": 3219,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3220",
      "ordinal": 3220,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3221",
      "ordinal": 3221,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次表达或行动、主体个案、候选参与总体、立场分布及聚合规则；X=空间范围：关系现场、组织空间、数字公共空间与跨域传播范围；T=时间跨度：表达—行动窗口、承诺周期、漂移与解耦时滞；O=组织层级：行动角色、团队、组织、制度至公共治理生态；C=因果层次：表达事件、意义—行动互动机制、中观协调结构、制度安排与系统条件；R=观察分辨率：原始表达与行动、事件序列、个案、立场分布、协调指标与摘要，并登记压缩损失；I=影响范围：直接参与者、异议者、间接受影响者、二阶协调后果、跨域与代际影响；N=网络拓扑范围：表达传播、协调连接、异质簇群与桥接节点；J=管辖与授权范围：锚点命名、代表性采用、协调或统一要求分别登记授权；必须保留异质锚点"
    },
    {
      "anchor": "V82-P3222",
      "ordinal": 3222,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3223",
      "ordinal": 3223,
      "style": "TableText",
      "text": "能改变资源或行动的目标、身份、记忆、承诺、恐惧或共同问题"
    },
    {
      "anchor": "V82-P3224",
      "ordinal": 3224,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3225",
      "ordinal": 3225,
      "style": "TableText",
      "text": "1. 意义到资源或行动的桥接"
    },
    {
      "anchor": "V82-P3226",
      "ordinal": 3226,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3227",
      "ordinal": 3227,
      "style": "TableText",
      "text": "1. 代表规则"
    },
    {
      "anchor": "V82-P3228",
      "ordinal": 3228,
      "style": "TableText",
      "text": "2. 异质性"
    },
    {
      "anchor": "V82-P3229",
      "ordinal": 3229,
      "style": "TableText",
      "text": "3. 成本收益分布"
    },
    {
      "anchor": "V82-P3230",
      "ordinal": 3230,
      "style": "TableText",
      "text": "4. J轴"
    },
    {
      "anchor": "V82-P3231",
      "ordinal": 3231,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3232",
      "ordinal": 3232,
      "style": "TableText",
      "text": "1. 锚点内容、强度和承载主体可改变"
    },
    {
      "anchor": "V82-P3233",
      "ordinal": 3233,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3234",
      "ordinal": 3234,
      "style": "TableText",
      "text": "1. 无意向、意义或承诺能力的非人系统"
    },
    {
      "anchor": "V82-P3235",
      "ordinal": 3235,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3236",
      "ordinal": 3236,
      "style": "TableText",
      "text": "1. 局部表达直接升级为共同意志"
    },
    {
      "anchor": "V82-P3237",
      "ordinal": 3237,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3238",
      "ordinal": 3238,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3239",
      "ordinal": 3239,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3240",
      "ordinal": 3240,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3241",
      "ordinal": 3241,
      "style": "TableText",
      "text": "1. 分散"
    },
    {
      "anchor": "V82-P3242",
      "ordinal": 3242,
      "style": "TableText",
      "text": "2. 凝聚"
    },
    {
      "anchor": "V82-P3243",
      "ordinal": 3243,
      "style": "TableText",
      "text": "3. 竞争"
    },
    {
      "anchor": "V82-P3244",
      "ordinal": 3244,
      "style": "TableText",
      "text": "4. 固化"
    },
    {
      "anchor": "V82-P3245",
      "ordinal": 3245,
      "style": "TableText",
      "text": "5. 解耦"
    },
    {
      "anchor": "V82-P3246",
      "ordinal": 3246,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3247",
      "ordinal": 3247,
      "style": "TableText",
      "text": "1. 预注册意义表达出现前后的资源配置差异"
    },
    {
      "anchor": "V82-P3248",
      "ordinal": 3248,
      "style": "TableText",
      "text": "2. 行动选择、协作完成率或冲突模式变化"
    },
    {
      "anchor": "V82-P3249",
      "ordinal": 3249,
      "style": "TableText",
      "text": "3. 不同位置对锚点的接受、拒绝与替代表述"
    },
    {
      "anchor": "V82-P3250",
      "ordinal": 3250,
      "style": "TableText",
      "text": "4. 比较条件下结果差异是否超过预定阈值"
    },
    {
      "anchor": "V82-P3251",
      "ordinal": 3251,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3252",
      "ordinal": 3252,
      "style": "TableText",
      "text": "1. 资源调整"
    },
    {
      "anchor": "V82-P3253",
      "ordinal": 3253,
      "style": "TableText",
      "text": "2. 行动序列"
    },
    {
      "anchor": "V82-P3254",
      "ordinal": 3254,
      "style": "TableText",
      "text": "3. 承诺与退出记录"
    },
    {
      "anchor": "V82-P3255",
      "ordinal": 3255,
      "style": "TableText",
      "text": "4. 冲突证据"
    },
    {
      "anchor": "V82-P3256",
      "ordinal": 3256,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3257",
      "ordinal": 3257,
      "style": "TableText",
      "text": "1. 参与位置2. 表达安全3. 资源与行动数据"
    },
    {
      "anchor": "V82-P3258",
      "ordinal": 3258,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3259",
      "ordinal": 3259,
      "style": "TableText",
      "text": "1. 生成事件2. 承接动员3. 规范选择议程"
    },
    {
      "anchor": "V82-P3260",
      "ordinal": 3260,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3261",
      "ordinal": 3261,
      "style": "TableText",
      "text": "区分短期口号、长期承诺与代际记忆"
    },
    {
      "anchor": "V82-P3262",
      "ordinal": 3262,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3263",
      "ordinal": 3263,
      "style": "TableText",
      "text": "记录沉默、强制一致与内部异质性"
    },
    {
      "anchor": "V82-P3264",
      "ordinal": 3264,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3265",
      "ordinal": 3265,
      "style": "TableText",
      "text": "低安全位置的不同目标不得被聚合抹去"
    },
    {
      "anchor": "V82-P3266",
      "ordinal": 3266,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3267",
      "ordinal": 3267,
      "style": "TableText",
      "text": "1. 认同者"
    },
    {
      "anchor": "V82-P3268",
      "ordinal": 3268,
      "style": "TableText",
      "text": "2. 异议者"
    },
    {
      "anchor": "V82-P3269",
      "ordinal": 3269,
      "style": "TableText",
      "text": "3. 被代表者"
    },
    {
      "anchor": "V82-P3270",
      "ordinal": 3270,
      "style": "TableText",
      "text": "4. 成本承担者"
    },
    {
      "anchor": "V82-P3271",
      "ordinal": 3271,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3272",
      "ordinal": 3272,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3273",
      "ordinal": 3273,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3274",
      "ordinal": 3274,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3275",
      "ordinal": 3275,
      "style": "TableText",
      "text": "1. 叙事"
    },
    {
      "anchor": "V82-P3276",
      "ordinal": 3276,
      "style": "TableText",
      "text": "2. 承诺"
    },
    {
      "anchor": "V82-P3277",
      "ordinal": 3277,
      "style": "TableText",
      "text": "3. 共同记忆"
    },
    {
      "anchor": "V82-P3278",
      "ordinal": 3278,
      "style": "TableText",
      "text": "4. 制度目标"
    },
    {
      "anchor": "V82-P3279",
      "ordinal": 3279,
      "style": "TableText",
      "text": "5. 问题定义"
    },
    {
      "anchor": "V82-P3280",
      "ordinal": 3280,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3281",
      "ordinal": 3281,
      "style": "TableText",
      "text": "1. 提出代表性主张者2. 据此配置资源者"
    },
    {
      "anchor": "V82-P3282",
      "ordinal": 3282,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3283",
      "ordinal": 3283,
      "style": "TableText",
      "text": "锚点存在不证明其正当"
    },
    {
      "anchor": "V82-P3284",
      "ordinal": 3284,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3285",
      "ordinal": 3285,
      "style": "TableText",
      "text": "有行动桥接时至解释级，无桥接时仅描述表达"
    },
    {
      "anchor": "V82-P3286",
      "ordinal": 3286,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3287",
      "ordinal": 3287,
      "style": "TableText",
      "text": "本变量只生成候选锚点、异质表达、比较结果与补证需求描述，不授权统一意义、代表意愿或协调行动；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3288",
      "ordinal": 3288,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3289",
      "ordinal": 3289,
      "style": "TableText",
      "text": "1. 反复出现的口号没有改变任何资源配置或行动"
    },
    {
      "anchor": "V82-P3290",
      "ordinal": 3290,
      "style": "TableText",
      "text": "2. 高压场景中的一致表达掩盖相互冲突的真实目标"
    },
    {
      "anchor": "V82-P3291",
      "ordinal": 3291,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3292",
      "ordinal": 3292,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，成员可经安全可达、反报复通道否认代表性、提交异质目标或拒绝被锚定，并触发与原锚点判断链独立的复核"
    },
    {
      "anchor": "V82-P3293",
      "ordinal": 3293,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3294",
      "ordinal": 3294,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销锚点命名、移除其代表性与下游协调效力并恢复异质表达状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3295",
      "ordinal": 3295,
      "style": "SecH2",
      "text": "A.4　HV04 生成节点（完整接口卡）"
    },
    {
      "anchor": "V82-P3296",
      "ordinal": 3296,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3297",
      "ordinal": 3297,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3298",
      "ordinal": 3298,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3299",
      "ordinal": 3299,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3300",
      "ordinal": 3300,
      "style": "TableText",
      "text": "HV04"
    },
    {
      "anchor": "V82-P3301",
      "ordinal": 3301,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3302",
      "ordinal": 3302,
      "style": "TableText",
      "text": "human_variable:HV04"
    },
    {
      "anchor": "V82-P3303",
      "ordinal": 3303,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3304",
      "ordinal": 3304,
      "style": "TableText",
      "text": "生成节点"
    },
    {
      "anchor": "V82-P3305",
      "ordinal": 3305,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3306",
      "ordinal": 3306,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3307",
      "ordinal": 3307,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3308",
      "ordinal": 3308,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3309",
      "ordinal": 3309,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3310",
      "ordinal": 3310,
      "style": "TableText",
      "text": "生成必须分流为生成条件GC、生成主体GS与生成事件GE，允许无可识别主体的涌现型生成。"
    },
    {
      "anchor": "V82-P3311",
      "ordinal": 3311,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3312",
      "ordinal": 3312,
      "style": "TableText",
      "text": "人类结构中新行动、组织、制度或状态转移的形成"
    },
    {
      "anchor": "V82-P3313",
      "ordinal": 3313,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3314",
      "ordinal": 3314,
      "style": "TableText",
      "text": "条件被人格化、事件被当作主体或主体资格不明"
    },
    {
      "anchor": "V82-P3315",
      "ordinal": 3315,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3316",
      "ordinal": 3316,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3317",
      "ordinal": 3317,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3318",
      "ordinal": 3318,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3319",
      "ordinal": 3319,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3320",
      "ordinal": 3320,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3321",
      "ordinal": 3321,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P3322",
      "ordinal": 3322,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3323",
      "ordinal": 3323,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3324",
      "ordinal": 3324,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3325",
      "ordinal": 3325,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3326",
      "ordinal": 3326,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3327",
      "ordinal": 3327,
      "style": "TableText",
      "text": "1. route_id=HV04-R0-generation-typing；"
    },
    {
      "anchor": "V82-P3328",
      "ordinal": 3328,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3329",
      "ordinal": 3329,
      "style": "TableText",
      "text": "when=GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；"
    },
    {
      "anchor": "V82-P3330",
      "ordinal": 3330,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3331",
      "ordinal": 3331,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3332",
      "ordinal": 3332,
      "style": "TableText",
      "text": "allowed_conclusion=分别登记候选生成条件、候选生成主体与候选生成事件，不将三者互相替代。；"
    },
    {
      "anchor": "V82-P3333",
      "ordinal": 3333,
      "style": "TableText",
      "text": "result_ceiling=只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。"
    },
    {
      "anchor": "V82-P3334",
      "ordinal": 3334,
      "style": "TableText",
      "text": "2. route_id=HV04-R1-generation-mechanism；"
    },
    {
      "anchor": "V82-P3335",
      "ordinal": 3335,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P3336",
      "ordinal": 3336,
      "style": "TableText",
      "text": "when=预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；"
    },
    {
      "anchor": "V82-P3337",
      "ordinal": 3337,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance；"
    },
    {
      "anchor": "V82-P3338",
      "ordinal": 3338,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3339",
      "ordinal": 3339,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定尺度、窗口和通道内的候选生成机制及其GC、GS、GE分型。；"
    },
    {
      "anchor": "V82-P3340",
      "ordinal": 3340,
      "style": "TableText",
      "text": "result_ceiling=不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。"
    },
    {
      "anchor": "V82-P3341",
      "ordinal": 3341,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3342",
      "ordinal": 3342,
      "style": "TableText",
      "text": "1. 条件性生成路径2. 有主体或无主体生成"
    },
    {
      "anchor": "V82-P3343",
      "ordinal": 3343,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3344",
      "ordinal": 3344,
      "style": "TableText",
      "text": "1. 技术或危机具有意图"
    },
    {
      "anchor": "V82-P3345",
      "ordinal": 3345,
      "style": "TableText",
      "text": "2. 生成主体自动拥有持续授权"
    },
    {
      "anchor": "V82-P3346",
      "ordinal": 3346,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3347",
      "ordinal": 3347,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3348",
      "ordinal": 3348,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3349",
      "ordinal": 3349,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3350",
      "ordinal": 3350,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：条件暴露、主体行动与生成事件单元，各自个案总体、分布及聚合规则；X=空间范围：生成现场、组织或平台边界、扩散区域与跨域环境；T=时间跨度：条件积累期、主体行动窗、事件时点与扩散时滞；O=组织层级：行动角色、生成团队、组织、制度至治理生态；C=因果层次：生成事件、主体—条件互动机制、中观生成结构、制度安排与系统条件；R=观察分辨率：原始条件行动事件、生成序列、个案、结果分布、转移指标与摘要，并登记压缩损失；I=影响范围：直接生成参与者、承接者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：条件传播、主体协作、事件扩散与涌现连接；J=管辖与授权范围：生成识别、启动改变、资源投入及扩散处置分别登记授权；GC、GS、GE分别登记尺度"
    },
    {
      "anchor": "V82-P3351",
      "ordinal": 3351,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3352",
      "ordinal": 3352,
      "style": "TableText",
      "text": "形成可检测状态转移的条件、主体与事件组合"
    },
    {
      "anchor": "V82-P3353",
      "ordinal": 3353,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3354",
      "ordinal": 3354,
      "style": "TableText",
      "text": "1. GC、GS、GE强类型分离"
    },
    {
      "anchor": "V82-P3355",
      "ordinal": 3355,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3356",
      "ordinal": 3356,
      "style": "TableText",
      "text": "1. 新单位与总体"
    },
    {
      "anchor": "V82-P3357",
      "ordinal": 3357,
      "style": "TableText",
      "text": "2. 代表关系"
    },
    {
      "anchor": "V82-P3358",
      "ordinal": 3358,
      "style": "TableText",
      "text": "3. 责任类型"
    },
    {
      "anchor": "V82-P3359",
      "ordinal": 3359,
      "style": "TableText",
      "text": "4. 外部影响"
    },
    {
      "anchor": "V82-P3360",
      "ordinal": 3360,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3361",
      "ordinal": 3361,
      "style": "TableText",
      "text": "1. 生成主体、条件与事件可随尺度改变"
    },
    {
      "anchor": "V82-P3362",
      "ordinal": 3362,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3363",
      "ordinal": 3363,
      "style": "TableText",
      "text": "1. 没有新状态形成或生成主张的稳定描述"
    },
    {
      "anchor": "V82-P3364",
      "ordinal": 3364,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3365",
      "ordinal": 3365,
      "style": "TableText",
      "text": "1. 把条件或事件升格为有意图主体"
    },
    {
      "anchor": "V82-P3366",
      "ordinal": 3366,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3367",
      "ordinal": 3367,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3368",
      "ordinal": 3368,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3369",
      "ordinal": 3369,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3370",
      "ordinal": 3370,
      "style": "TableText",
      "text": "1. 潜在"
    },
    {
      "anchor": "V82-P3371",
      "ordinal": 3371,
      "style": "TableText",
      "text": "2. 触发"
    },
    {
      "anchor": "V82-P3372",
      "ordinal": 3372,
      "style": "TableText",
      "text": "3. 形成"
    },
    {
      "anchor": "V82-P3373",
      "ordinal": 3373,
      "style": "TableText",
      "text": "4. 中断"
    },
    {
      "anchor": "V82-P3374",
      "ordinal": 3374,
      "style": "TableText",
      "text": "5. 扩散"
    },
    {
      "anchor": "V82-P3375",
      "ordinal": 3375,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3376",
      "ordinal": 3376,
      "style": "TableText",
      "text": "1. 候选条件出现、改变或移除的时间记录"
    },
    {
      "anchor": "V82-P3377",
      "ordinal": 3377,
      "style": "TableText",
      "text": "2. 生成主体的能力、授权、决策与实际行动"
    },
    {
      "anchor": "V82-P3378",
      "ordinal": 3378,
      "style": "TableText",
      "text": "3. 生成事件前后预注册状态转移"
    },
    {
      "anchor": "V82-P3379",
      "ordinal": 3379,
      "style": "TableText",
      "text": "4. 无主体涌现时局部互动与总体结果的桥接记录"
    },
    {
      "anchor": "V82-P3380",
      "ordinal": 3380,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3381",
      "ordinal": 3381,
      "style": "TableText",
      "text": "1. 启动记录"
    },
    {
      "anchor": "V82-P3382",
      "ordinal": 3382,
      "style": "TableText",
      "text": "2. 条件窗口"
    },
    {
      "anchor": "V82-P3383",
      "ordinal": 3383,
      "style": "TableText",
      "text": "3. 主体行动"
    },
    {
      "anchor": "V82-P3384",
      "ordinal": 3384,
      "style": "TableText",
      "text": "4. 无主体互动机制"
    },
    {
      "anchor": "V82-P3385",
      "ordinal": 3385,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3386",
      "ordinal": 3386,
      "style": "TableText",
      "text": "1. 指向锚点2. 资源与制度条件3. 因果合同"
    },
    {
      "anchor": "V82-P3387",
      "ordinal": 3387,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3388",
      "ordinal": 3388,
      "style": "TableText",
      "text": "1. 承接需求2. 状态转移3. 责任链起点"
    },
    {
      "anchor": "V82-P3389",
      "ordinal": 3389,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3390",
      "ordinal": 3390,
      "style": "TableText",
      "text": "登记条件积累、触发事件与形成时滞"
    },
    {
      "anchor": "V82-P3391",
      "ordinal": 3391,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3392",
      "ordinal": 3392,
      "style": "TableText",
      "text": "记录共同生成、无主体涌现和不可识别主体"
    },
    {
      "anchor": "V82-P3393",
      "ordinal": 3393,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3394",
      "ordinal": 3394,
      "style": "TableText",
      "text": "被遗漏的非正式启动者与受影响位置"
    },
    {
      "anchor": "V82-P3395",
      "ordinal": 3395,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3396",
      "ordinal": 3396,
      "style": "TableText",
      "text": "1. 启动者"
    },
    {
      "anchor": "V82-P3397",
      "ordinal": 3397,
      "style": "TableText",
      "text": "2. 承接者"
    },
    {
      "anchor": "V82-P3398",
      "ordinal": 3398,
      "style": "TableText",
      "text": "3. 受益者"
    },
    {
      "anchor": "V82-P3399",
      "ordinal": 3399,
      "style": "TableText",
      "text": "4. 受影响者"
    },
    {
      "anchor": "V82-P3400",
      "ordinal": 3400,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3401",
      "ordinal": 3401,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3402",
      "ordinal": 3402,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3403",
      "ordinal": 3403,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3404",
      "ordinal": 3404,
      "style": "TableText",
      "text": "1. 启动者"
    },
    {
      "anchor": "V82-P3405",
      "ordinal": 3405,
      "style": "TableText",
      "text": "2. 程序"
    },
    {
      "anchor": "V82-P3406",
      "ordinal": 3406,
      "style": "TableText",
      "text": "3. 技术设施"
    },
    {
      "anchor": "V82-P3407",
      "ordinal": 3407,
      "style": "TableText",
      "text": "4. 关系网络"
    },
    {
      "anchor": "V82-P3408",
      "ordinal": 3408,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3409",
      "ordinal": 3409,
      "style": "TableText",
      "text": "1. 实际行动者2. 决策者3. 授权者"
    },
    {
      "anchor": "V82-P3410",
      "ordinal": 3410,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3411",
      "ordinal": 3411,
      "style": "TableText",
      "text": "生成事实不证明正当或责任完整"
    },
    {
      "anchor": "V82-P3412",
      "ordinal": 3412,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3413",
      "ordinal": 3413,
      "style": "TableText",
      "text": "机制链完整时至解释级"
    },
    {
      "anchor": "V82-P3414",
      "ordinal": 3414,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3415",
      "ordinal": 3415,
      "style": "TableText",
      "text": "本变量只生成GC、GS、GE候选分型、状态转移描述与补证需求，不授权启动、扩散或停止生成过程；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3416",
      "ordinal": 3416,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3417",
      "ordinal": 3417,
      "style": "TableText",
      "text": "1. 技术条件被错误描述成具有目标的生成主体"
    },
    {
      "anchor": "V82-P3418",
      "ordinal": 3418,
      "style": "TableText",
      "text": "2. 无统一发起者的涌现过程被强行归因给一个可见人物"
    },
    {
      "anchor": "V82-P3419",
      "ordinal": 3419,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3420",
      "ordinal": 3420,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，被归为生成主体者可经安全可达、反报复通道挑战意图、角色与授权归因，并触发与原分型或决策链独立的复核"
    },
    {
      "anchor": "V82-P3421",
      "ordinal": 3421,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3422",
      "ordinal": 3422,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正GC、GS、GE类型，实际移除错误意图或责任归因及其下游效力，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3423",
      "ordinal": 3423,
      "style": "SecH2",
      "text": "A.5　HV05 行动承接层（完整接口卡）"
    },
    {
      "anchor": "V82-P3424",
      "ordinal": 3424,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3425",
      "ordinal": 3425,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3426",
      "ordinal": 3426,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3427",
      "ordinal": 3427,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3428",
      "ordinal": 3428,
      "style": "TableText",
      "text": "HV05"
    },
    {
      "anchor": "V82-P3429",
      "ordinal": 3429,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3430",
      "ordinal": 3430,
      "style": "TableText",
      "text": "human_variable:HV05"
    },
    {
      "anchor": "V82-P3431",
      "ordinal": 3431,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3432",
      "ordinal": 3432,
      "style": "TableText",
      "text": "行动承接层"
    },
    {
      "anchor": "V82-P3433",
      "ordinal": 3433,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3434",
      "ordinal": 3434,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3435",
      "ordinal": 3435,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3436",
      "ordinal": 3436,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3437",
      "ordinal": 3437,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3438",
      "ordinal": 3438,
      "style": "TableText",
      "text": "执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。"
    },
    {
      "anchor": "V82-P3439",
      "ordinal": 3439,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3440",
      "ordinal": 3440,
      "style": "TableText",
      "text": "需要持续行动、维护、照护或执行的人类结构"
    },
    {
      "anchor": "V82-P3441",
      "ordinal": 3441,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3442",
      "ordinal": 3442,
      "style": "TableText",
      "text": "低权限执行者被默认归为主要责任人或承接能力被当作义务"
    },
    {
      "anchor": "V82-P3443",
      "ordinal": 3443,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3444",
      "ordinal": 3444,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3445",
      "ordinal": 3445,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3446",
      "ordinal": 3446,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3447",
      "ordinal": 3447,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3448",
      "ordinal": 3448,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3449",
      "ordinal": 3449,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P3450",
      "ordinal": 3450,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3451",
      "ordinal": 3451,
      "style": "TableText",
      "text": "1. H2"
    },
    {
      "anchor": "V82-P3452",
      "ordinal": 3452,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3453",
      "ordinal": 3453,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3454",
      "ordinal": 3454,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3455",
      "ordinal": 3455,
      "style": "TableText",
      "text": "1. route_id=HV05-R0-carrier-responsibility-split；"
    },
    {
      "anchor": "V82-P3456",
      "ordinal": 3456,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3457",
      "ordinal": 3457,
      "style": "TableText",
      "text": "when=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；"
    },
    {
      "anchor": "V82-P3458",
      "ordinal": 3458,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3459",
      "ordinal": 3459,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3460",
      "ordinal": 3460,
      "style": "TableText",
      "text": "allowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；"
    },
    {
      "anchor": "V82-P3461",
      "ordinal": 3461,
      "style": "TableText",
      "text": "result_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。"
    },
    {
      "anchor": "V82-P3462",
      "ordinal": 3462,
      "style": "TableText",
      "text": "2. route_id=HV05-R1-functional-carrier-effect；"
    },
    {
      "anchor": "V82-P3463",
      "ordinal": 3463,
      "style": "TableText",
      "text": "claim_level=conditional_effect；"
    },
    {
      "anchor": "V82-P3464",
      "ordinal": 3464,
      "style": "TableText",
      "text": "when=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；"
    },
    {
      "anchor": "V82-P3465",
      "ordinal": 3465,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance；"
    },
    {
      "anchor": "V82-P3466",
      "ordinal": 3466,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3467",
      "ordinal": 3467,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；"
    },
    {
      "anchor": "V82-P3468",
      "ordinal": 3468,
      "style": "TableText",
      "text": "result_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。"
    },
    {
      "anchor": "V82-P3469",
      "ordinal": 3469,
      "style": "TableText",
      "text": "3. route_id=HV05-R2-intertemporal-reproduction；"
    },
    {
      "anchor": "V82-P3470",
      "ordinal": 3470,
      "style": "TableText",
      "text": "claim_level=intertemporal_explanation；"
    },
    {
      "anchor": "V82-P3471",
      "ordinal": 3471,
      "style": "TableText",
      "text": "when=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；"
    },
    {
      "anchor": "V82-P3472",
      "ordinal": 3472,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance、G3-instance；"
    },
    {
      "anchor": "V82-P3473",
      "ordinal": 3473,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3474",
      "ordinal": 3474,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定窗口与载体内的跨期承接或再生产候选。；"
    },
    {
      "anchor": "V82-P3475",
      "ordinal": 3475,
      "style": "TableText",
      "text": "result_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。"
    },
    {
      "anchor": "V82-P3476",
      "ordinal": 3476,
      "style": "TableText",
      "text": "4. route_id=HV05-R3-historical-carrier-trace；"
    },
    {
      "anchor": "V82-P3477",
      "ordinal": 3477,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3478",
      "ordinal": 3478,
      "style": "TableText",
      "text": "when=H5-instance对唯一预选的具体载体与持久判据取得supported。；"
    },
    {
      "anchor": "V82-P3479",
      "ordinal": 3479,
      "style": "TableText",
      "text": "additional_inferential_requires=H5-instance；"
    },
    {
      "anchor": "V82-P3480",
      "ordinal": 3480,
      "style": "TableText",
      "text": "additional_protocol_requires=E4；"
    },
    {
      "anchor": "V82-P3481",
      "ordinal": 3481,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；"
    },
    {
      "anchor": "V82-P3482",
      "ordinal": 3482,
      "style": "TableText",
      "text": "result_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。"
    },
    {
      "anchor": "V82-P3483",
      "ordinal": 3483,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3484",
      "ordinal": 3484,
      "style": "TableText",
      "text": "1. 承接缺口2. 任务资源错配3. 责任分流"
    },
    {
      "anchor": "V82-P3485",
      "ordinal": 3485,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3486",
      "ordinal": 3486,
      "style": "TableText",
      "text": "1. 最可见者等于主要责任人"
    },
    {
      "anchor": "V82-P3487",
      "ordinal": 3487,
      "style": "TableText",
      "text": "2. 能承担所以应承担"
    },
    {
      "anchor": "V82-P3488",
      "ordinal": 3488,
      "style": "TableText",
      "text": "3. 非人载体承担责任"
    },
    {
      "anchor": "V82-P3489",
      "ordinal": 3489,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3490",
      "ordinal": 3490,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3491",
      "ordinal": 3491,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3492",
      "ordinal": 3492,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3493",
      "ordinal": 3493,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度"
    },
    {
      "anchor": "V82-P3494",
      "ordinal": 3494,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3495",
      "ordinal": 3495,
      "style": "TableText",
      "text": "实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度"
    },
    {
      "anchor": "V82-P3496",
      "ordinal": 3496,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3497",
      "ordinal": 3497,
      "style": "TableText",
      "text": "1. CV不等于RS"
    },
    {
      "anchor": "V82-P3498",
      "ordinal": 3498,
      "style": "TableText",
      "text": "2. 成本与受益分别登记"
    },
    {
      "anchor": "V82-P3499",
      "ordinal": 3499,
      "style": "TableText",
      "text": "3. 停止权"
    },
    {
      "anchor": "V82-P3500",
      "ordinal": 3500,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3501",
      "ordinal": 3501,
      "style": "TableText",
      "text": "1. 任务聚合"
    },
    {
      "anchor": "V82-P3502",
      "ordinal": 3502,
      "style": "TableText",
      "text": "2. 代表和委托"
    },
    {
      "anchor": "V82-P3503",
      "ordinal": 3503,
      "style": "TableText",
      "text": "3. 六类责任"
    },
    {
      "anchor": "V82-P3504",
      "ordinal": 3504,
      "style": "TableText",
      "text": "4. 外部成本"
    },
    {
      "anchor": "V82-P3505",
      "ordinal": 3505,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3506",
      "ordinal": 3506,
      "style": "TableText",
      "text": "1. 承接载体和责任主体可随层级改变"
    },
    {
      "anchor": "V82-P3507",
      "ordinal": 3507,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3508",
      "ordinal": 3508,
      "style": "TableText",
      "text": "1. 无主体行动、责任或维护要求的非人过程"
    },
    {
      "anchor": "V82-P3509",
      "ordinal": 3509,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3510",
      "ordinal": 3510,
      "style": "TableText",
      "text": "1. 个体承接直接等于组织责任"
    },
    {
      "anchor": "V82-P3511",
      "ordinal": 3511,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3512",
      "ordinal": 3512,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3513",
      "ordinal": 3513,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3514",
      "ordinal": 3514,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3515",
      "ordinal": 3515,
      "style": "TableText",
      "text": "1. 充足"
    },
    {
      "anchor": "V82-P3516",
      "ordinal": 3516,
      "style": "TableText",
      "text": "2. 脆弱"
    },
    {
      "anchor": "V82-P3517",
      "ordinal": 3517,
      "style": "TableText",
      "text": "3. 过载"
    },
    {
      "anchor": "V82-P3518",
      "ordinal": 3518,
      "style": "TableText",
      "text": "4. 断裂"
    },
    {
      "anchor": "V82-P3519",
      "ordinal": 3519,
      "style": "TableText",
      "text": "5. 替代"
    },
    {
      "anchor": "V82-P3520",
      "ordinal": 3520,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3521",
      "ordinal": 3521,
      "style": "TableText",
      "text": "1. 任务实际执行、维护、记录与修复日志"
    },
    {
      "anchor": "V82-P3522",
      "ordinal": 3522,
      "style": "TableText",
      "text": "2. 资源、容量、时间和成本流向"
    },
    {
      "anchor": "V82-P3523",
      "ordinal": 3523,
      "style": "TableText",
      "text": "3. 停止权、替代安排与承接转移记录"
    },
    {
      "anchor": "V82-P3524",
      "ordinal": 3524,
      "style": "TableText",
      "text": "4. 决策、授权、监督、受益与补救依据"
    },
    {
      "anchor": "V82-P3525",
      "ordinal": 3525,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3526",
      "ordinal": 3526,
      "style": "TableText",
      "text": "1. 任务流"
    },
    {
      "anchor": "V82-P3527",
      "ordinal": 3527,
      "style": "TableText",
      "text": "2. 工时与资源"
    },
    {
      "anchor": "V82-P3528",
      "ordinal": 3528,
      "style": "TableText",
      "text": "3. 维护记录"
    },
    {
      "anchor": "V82-P3529",
      "ordinal": 3529,
      "style": "TableText",
      "text": "4. 停止和拒绝记录"
    },
    {
      "anchor": "V82-P3530",
      "ordinal": 3530,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3531",
      "ordinal": 3531,
      "style": "TableText",
      "text": "1. 生成需求2. 资源3. 授权4. 角色"
    },
    {
      "anchor": "V82-P3532",
      "ordinal": 3532,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3533",
      "ordinal": 3533,
      "style": "TableText",
      "text": "1. 实现状态转移2. 成本分布3. 结构负荷"
    },
    {
      "anchor": "V82-P3534",
      "ordinal": 3534,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3535",
      "ordinal": 3535,
      "style": "TableText",
      "text": "登记排班、维护周期、积压与恢复时滞"
    },
    {
      "anchor": "V82-P3536",
      "ordinal": 3536,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3537",
      "ordinal": 3537,
      "style": "TableText",
      "text": "记录隐性劳动、非正式照护和边界外成本"
    },
    {
      "anchor": "V82-P3538",
      "ordinal": 3538,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3539",
      "ordinal": 3539,
      "style": "TableText",
      "text": "低权限、非正式与不可退出承接者"
    },
    {
      "anchor": "V82-P3540",
      "ordinal": 3540,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3541",
      "ordinal": 3541,
      "style": "TableText",
      "text": "1. 承接者"
    },
    {
      "anchor": "V82-P3542",
      "ordinal": 3542,
      "style": "TableText",
      "text": "2. 受益者"
    },
    {
      "anchor": "V82-P3543",
      "ordinal": 3543,
      "style": "TableText",
      "text": "3. 被服务者"
    },
    {
      "anchor": "V82-P3544",
      "ordinal": 3544,
      "style": "TableText",
      "text": "4. 替代者"
    },
    {
      "anchor": "V82-P3545",
      "ordinal": 3545,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3546",
      "ordinal": 3546,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3547",
      "ordinal": 3547,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3548",
      "ordinal": 3548,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3549",
      "ordinal": 3549,
      "style": "TableText",
      "text": "1. 人员"
    },
    {
      "anchor": "V82-P3550",
      "ordinal": 3550,
      "style": "TableText",
      "text": "2. 岗位"
    },
    {
      "anchor": "V82-P3551",
      "ordinal": 3551,
      "style": "TableText",
      "text": "3. 程序"
    },
    {
      "anchor": "V82-P3552",
      "ordinal": 3552,
      "style": "TableText",
      "text": "4. 设施"
    },
    {
      "anchor": "V82-P3553",
      "ordinal": 3553,
      "style": "TableText",
      "text": "5. 制度"
    },
    {
      "anchor": "V82-P3554",
      "ordinal": 3554,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3555",
      "ordinal": 3555,
      "style": "TableText",
      "text": "1. 行为责任者"
    },
    {
      "anchor": "V82-P3556",
      "ordinal": 3556,
      "style": "TableText",
      "text": "2. 决策责任者"
    },
    {
      "anchor": "V82-P3557",
      "ordinal": 3557,
      "style": "TableText",
      "text": "3. 授权责任者"
    },
    {
      "anchor": "V82-P3558",
      "ordinal": 3558,
      "style": "TableText",
      "text": "4. 监督责任者"
    },
    {
      "anchor": "V82-P3559",
      "ordinal": 3559,
      "style": "TableText",
      "text": "5. 受益责任者"
    },
    {
      "anchor": "V82-P3560",
      "ordinal": 3560,
      "style": "TableText",
      "text": "6. 补救责任者"
    },
    {
      "anchor": "V82-P3561",
      "ordinal": 3561,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3562",
      "ordinal": 3562,
      "style": "TableText",
      "text": "承接事实不产生继续承担义务"
    },
    {
      "anchor": "V82-P3563",
      "ordinal": 3563,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3564",
      "ordinal": 3564,
      "style": "TableText",
      "text": "资源与责任链完整时至诊断级"
    },
    {
      "anchor": "V82-P3565",
      "ordinal": 3565,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3566",
      "ordinal": 3566,
      "style": "TableText",
      "text": "本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3567",
      "ordinal": 3567,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3568",
      "ordinal": 3568,
      "style": "TableText",
      "text": "1. 最可见的低权限执行者不是决策、授权或受益责任主体"
    },
    {
      "anchor": "V82-P3569",
      "ordinal": 3569,
      "style": "TableText",
      "text": "2. 自动化设施承担传导任务但不能承担道德或法律责任"
    },
    {
      "anchor": "V82-P3570",
      "ordinal": 3570,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3571",
      "ordinal": 3571,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核"
    },
    {
      "anchor": "V82-P3572",
      "ordinal": 3572,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3573",
      "ordinal": 3573,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3574",
      "ordinal": 3574,
      "style": "SecH2",
      "text": "A.6　HV06 动力—承接链（完整接口卡）"
    },
    {
      "anchor": "V82-P3575",
      "ordinal": 3575,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3576",
      "ordinal": 3576,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3577",
      "ordinal": 3577,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3578",
      "ordinal": 3578,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3579",
      "ordinal": 3579,
      "style": "TableText",
      "text": "HV06"
    },
    {
      "anchor": "V82-P3580",
      "ordinal": 3580,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3581",
      "ordinal": 3581,
      "style": "TableText",
      "text": "human_variable:HV06"
    },
    {
      "anchor": "V82-P3582",
      "ordinal": 3582,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3583",
      "ordinal": 3583,
      "style": "TableText",
      "text": "动力—承接链"
    },
    {
      "anchor": "V82-P3584",
      "ordinal": 3584,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3585",
      "ordinal": 3585,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3586",
      "ordinal": 3586,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3587",
      "ordinal": 3587,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3588",
      "ordinal": 3588,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3589",
      "ordinal": 3589,
      "style": "TableText",
      "text": "从指向、生成到执行、维护与偿付的链条必须逐段登记通道、资源、成本、责任和时滞。"
    },
    {
      "anchor": "V82-P3590",
      "ordinal": 3590,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3591",
      "ordinal": 3591,
      "style": "TableText",
      "text": "人类集体行动、项目、组织与制度运行"
    },
    {
      "anchor": "V82-P3592",
      "ordinal": 3592,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3593",
      "ordinal": 3593,
      "style": "TableText",
      "text": "用热情、愿景或命令替代承接与偿付证据"
    },
    {
      "anchor": "V82-P3594",
      "ordinal": 3594,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3595",
      "ordinal": 3595,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3596",
      "ordinal": 3596,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3597",
      "ordinal": 3597,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3598",
      "ordinal": 3598,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3599",
      "ordinal": 3599,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3600",
      "ordinal": 3600,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P3601",
      "ordinal": 3601,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3602",
      "ordinal": 3602,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3603",
      "ordinal": 3603,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3604",
      "ordinal": 3604,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3605",
      "ordinal": 3605,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3606",
      "ordinal": 3606,
      "style": "TableText",
      "text": "1. route_id=HV06-R0-segment-map；"
    },
    {
      "anchor": "V82-P3607",
      "ordinal": 3607,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3608",
      "ordinal": 3608,
      "style": "TableText",
      "text": "when=至少一个链段的输入、输出、时延、损耗、中断、资源、成本与边界可观察。；"
    },
    {
      "anchor": "V82-P3609",
      "ordinal": 3609,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3610",
      "ordinal": 3610,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3611",
      "ordinal": 3611,
      "style": "TableText",
      "text": "allowed_conclusion=登记局部链段、缺失桥、时滞、损耗、中断点与成本位置。；"
    },
    {
      "anchor": "V82-P3612",
      "ordinal": 3612,
      "style": "TableText",
      "text": "result_ceiling=不得由单一链段或动力语言宣称完整链条或有效通道。"
    },
    {
      "anchor": "V82-P3613",
      "ordinal": 3613,
      "style": "TableText",
      "text": "2. route_id=HV06-R1-complete-chain-composition；"
    },
    {
      "anchor": "V82-P3614",
      "ordinal": 3614,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3615",
      "ordinal": 3615,
      "style": "TableText",
      "text": "when=指向、生成与承接三个接口记录可在同一对象、尺度、窗口与量的映射中逐段连接。；"
    },
    {
      "anchor": "V82-P3616",
      "ordinal": 3616,
      "style": "TableText",
      "text": "additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05；"
    },
    {
      "anchor": "V82-P3617",
      "ordinal": 3617,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3618",
      "ordinal": 3618,
      "style": "TableText",
      "text": "allowed_conclusion=登记完整候选动力—承接链及逐段证据覆盖。；"
    },
    {
      "anchor": "V82-P3619",
      "ordinal": 3619,
      "style": "TableText",
      "text": "result_ceiling=只到候选链条组成；接口记录齐全不等于各链段具有因果效力。"
    },
    {
      "anchor": "V82-P3620",
      "ordinal": 3620,
      "style": "TableText",
      "text": "3. route_id=HV06-R2-effective-channel；"
    },
    {
      "anchor": "V82-P3621",
      "ordinal": 3621,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P3622",
      "ordinal": 3622,
      "style": "TableText",
      "text": "when=完整候选链已组成，且符合资格的G2-instance逐段识别指定通道对目标转移的效应。；"
    },
    {
      "anchor": "V82-P3623",
      "ordinal": 3623,
      "style": "TableText",
      "text": "additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05、G2-instance；"
    },
    {
      "anchor": "V82-P3624",
      "ordinal": 3624,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3625",
      "ordinal": 3625,
      "style": "TableText",
      "text": "allowed_conclusion=登记已检验链段和窗口内的有效动力—承接通道、损耗与中断机制。；"
    },
    {
      "anchor": "V82-P3626",
      "ordinal": 3626,
      "style": "TableText",
      "text": "result_ceiling=不得从一次贯通推出跨期再生产、责任、正当性或行动授权。"
    },
    {
      "anchor": "V82-P3627",
      "ordinal": 3627,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3628",
      "ordinal": 3628,
      "style": "TableText",
      "text": "1. 链条瓶颈2. 动力与承接脱节3. 隐性偿付"
    },
    {
      "anchor": "V82-P3629",
      "ordinal": 3629,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3630",
      "ordinal": 3630,
      "style": "TableText",
      "text": "1. 动力强等于可持续"
    },
    {
      "anchor": "V82-P3631",
      "ordinal": 3631,
      "style": "TableText",
      "text": "2. 失败归因意愿不足"
    },
    {
      "anchor": "V82-P3632",
      "ordinal": 3632,
      "style": "TableText",
      "text": "3. 承接者应自行补洞"
    },
    {
      "anchor": "V82-P3633",
      "ordinal": 3633,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3634",
      "ordinal": 3634,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3635",
      "ordinal": 3635,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3636",
      "ordinal": 3636,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3637",
      "ordinal": 3637,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单个链节事件、链条个案、同类链总体、输入输出分布及聚合规则；X=空间范围：行动现场、项目或组织边界、数字协作空间与跨域外溢；T=时间跨度：启动、维持、中断、恢复窗口及跨期周期；O=组织层级：发起角色、执行团队、组织、制度至治理生态；C=因果层次：链节事件、动力—资源—任务互动机制、中观承接链、制度安排与系统条件；R=观察分辨率：原始任务资源记录、链节序列、链条个案、损耗分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接发起与承接位置、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖链、替代路径、瓶颈、反馈连接与跨域桥接；J=管辖与授权范围：目标采用、任务分配、资源投入、停止与试验分别登记授权；逐段标明跨轴位置"
    },
    {
      "anchor": "V82-P3638",
      "ordinal": 3638,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3639",
      "ordinal": 3639,
      "style": "TableText",
      "text": "把指向和生成转为持续行动的可追踪链条"
    },
    {
      "anchor": "V82-P3640",
      "ordinal": 3640,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3641",
      "ordinal": 3641,
      "style": "TableText",
      "text": "1. 指向、生成、承接、资源、成本和责任链"
    },
    {
      "anchor": "V82-P3642",
      "ordinal": 3642,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3643",
      "ordinal": 3643,
      "style": "TableText",
      "text": "1. 跨层桥接"
    },
    {
      "anchor": "V82-P3644",
      "ordinal": 3644,
      "style": "TableText",
      "text": "2. 聚合损失"
    },
    {
      "anchor": "V82-P3645",
      "ordinal": 3645,
      "style": "TableText",
      "text": "3. 责任继承"
    },
    {
      "anchor": "V82-P3646",
      "ordinal": 3646,
      "style": "TableText",
      "text": "4. 保护底板"
    },
    {
      "anchor": "V82-P3647",
      "ordinal": 3647,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3648",
      "ordinal": 3648,
      "style": "TableText",
      "text": "1. 节点、通道和瓶颈可随组织尺度改变"
    },
    {
      "anchor": "V82-P3649",
      "ordinal": 3649,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3650",
      "ordinal": 3650,
      "style": "TableText",
      "text": "1. 无意向动力与人类承接的非人过程"
    },
    {
      "anchor": "V82-P3651",
      "ordinal": 3651,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3652",
      "ordinal": 3652,
      "style": "TableText",
      "text": "1. 局部动力或单一节点直接代表完整链条"
    },
    {
      "anchor": "V82-P3653",
      "ordinal": 3653,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3654",
      "ordinal": 3654,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3655",
      "ordinal": 3655,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3656",
      "ordinal": 3656,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3657",
      "ordinal": 3657,
      "style": "TableText",
      "text": "1. 贯通"
    },
    {
      "anchor": "V82-P3658",
      "ordinal": 3658,
      "style": "TableText",
      "text": "2. 迟滞"
    },
    {
      "anchor": "V82-P3659",
      "ordinal": 3659,
      "style": "TableText",
      "text": "3. 过载"
    },
    {
      "anchor": "V82-P3660",
      "ordinal": 3660,
      "style": "TableText",
      "text": "4. 断裂"
    },
    {
      "anchor": "V82-P3661",
      "ordinal": 3661,
      "style": "TableText",
      "text": "5. 替代"
    },
    {
      "anchor": "V82-P3662",
      "ordinal": 3662,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3663",
      "ordinal": 3663,
      "style": "TableText",
      "text": "1. 锚点转化为任务、预算、规则或排程的记录"
    },
    {
      "anchor": "V82-P3664",
      "ordinal": 3664,
      "style": "TableText",
      "text": "2. 每段输入输出、时延、损耗与中断点"
    },
    {
      "anchor": "V82-P3665",
      "ordinal": 3665,
      "style": "TableText",
      "text": "3. 承接者容量、停止与替代路径变化"
    },
    {
      "anchor": "V82-P3666",
      "ordinal": 3666,
      "style": "TableText",
      "text": "4. 链条输出对目标结果的实际贡献"
    },
    {
      "anchor": "V82-P3667",
      "ordinal": 3667,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3668",
      "ordinal": 3668,
      "style": "TableText",
      "text": "1. 资源流"
    },
    {
      "anchor": "V82-P3669",
      "ordinal": 3669,
      "style": "TableText",
      "text": "2. 任务与维护记录"
    },
    {
      "anchor": "V82-P3670",
      "ordinal": 3670,
      "style": "TableText",
      "text": "3. 偿付与成本"
    },
    {
      "anchor": "V82-P3671",
      "ordinal": 3671,
      "style": "TableText",
      "text": "4. 时滞"
    },
    {
      "anchor": "V82-P3672",
      "ordinal": 3672,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3673",
      "ordinal": 3673,
      "style": "TableText",
      "text": "1. 指向锚点2. 生成节点3. 承接层"
    },
    {
      "anchor": "V82-P3674",
      "ordinal": 3674,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3675",
      "ordinal": 3675,
      "style": "TableText",
      "text": "1. 行动结果2. 负荷3. 反馈与演化痕迹"
    },
    {
      "anchor": "V82-P3676",
      "ordinal": 3676,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3677",
      "ordinal": 3677,
      "style": "TableText",
      "text": "逐段登记启动、传导、维护和偿付时滞"
    },
    {
      "anchor": "V82-P3678",
      "ordinal": 3678,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3679",
      "ordinal": 3679,
      "style": "TableText",
      "text": "记录断点、替代通道与边界外偿付"
    },
    {
      "anchor": "V82-P3680",
      "ordinal": 3680,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3681",
      "ordinal": 3681,
      "style": "TableText",
      "text": "非正式、低可见和跨组织承接位置"
    },
    {
      "anchor": "V82-P3682",
      "ordinal": 3682,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3683",
      "ordinal": 3683,
      "style": "TableText",
      "text": "1. 发起者"
    },
    {
      "anchor": "V82-P3684",
      "ordinal": 3684,
      "style": "TableText",
      "text": "2. 承接者"
    },
    {
      "anchor": "V82-P3685",
      "ordinal": 3685,
      "style": "TableText",
      "text": "3. 受益者"
    },
    {
      "anchor": "V82-P3686",
      "ordinal": 3686,
      "style": "TableText",
      "text": "4. 成本承担者"
    },
    {
      "anchor": "V82-P3687",
      "ordinal": 3687,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3688",
      "ordinal": 3688,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3689",
      "ordinal": 3689,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3690",
      "ordinal": 3690,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3691",
      "ordinal": 3691,
      "style": "TableText",
      "text": "1. 人员与岗位"
    },
    {
      "anchor": "V82-P3692",
      "ordinal": 3692,
      "style": "TableText",
      "text": "2. 程序"
    },
    {
      "anchor": "V82-P3693",
      "ordinal": 3693,
      "style": "TableText",
      "text": "3. 预算"
    },
    {
      "anchor": "V82-P3694",
      "ordinal": 3694,
      "style": "TableText",
      "text": "4. 基础设施"
    },
    {
      "anchor": "V82-P3695",
      "ordinal": 3695,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3696",
      "ordinal": 3696,
      "style": "TableText",
      "text": "1. 各节点行为、决策、授权、监督与补救责任者"
    },
    {
      "anchor": "V82-P3697",
      "ordinal": 3697,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3698",
      "ordinal": 3698,
      "style": "TableText",
      "text": "链条有效不证明目标正当"
    },
    {
      "anchor": "V82-P3699",
      "ordinal": 3699,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3700",
      "ordinal": 3700,
      "style": "TableText",
      "text": "全链证据充分时至解释或诊断级"
    },
    {
      "anchor": "V82-P3701",
      "ordinal": 3701,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3702",
      "ordinal": 3702,
      "style": "TableText",
      "text": "本变量只生成链条连通、时滞、损耗、中断、成本与承接需求描述，不授权减载、资源调整或试验；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3703",
      "ordinal": 3703,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3704",
      "ordinal": 3704,
      "style": "TableText",
      "text": "1. 强烈愿景和集中动员没有持续资源、维护或偿付"
    },
    {
      "anchor": "V82-P3705",
      "ordinal": 3705,
      "style": "TableText",
      "text": "2. 表面贯通的链条把关键成本转移给边界外承接者"
    },
    {
      "anchor": "V82-P3706",
      "ordinal": 3706,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3707",
      "ordinal": 3707,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，链上承接或受影响位置可经安全可达、反报复通道挑战资源、成本与链条归因，并触发与原链条判断或决策链独立的复核"
    },
    {
      "anchor": "V82-P3708",
      "ordinal": 3708,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3709",
      "ordinal": 3709,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销整体链条归因及其下游效力、恢复为节点级描述与未决状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3710",
      "ordinal": 3710,
      "style": "SecH2",
      "text": "A.7　HV07 反馈写回（完整接口卡）"
    },
    {
      "anchor": "V82-P3711",
      "ordinal": 3711,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3712",
      "ordinal": 3712,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3713",
      "ordinal": 3713,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3714",
      "ordinal": 3714,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3715",
      "ordinal": 3715,
      "style": "TableText",
      "text": "HV07"
    },
    {
      "anchor": "V82-P3716",
      "ordinal": 3716,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3717",
      "ordinal": 3717,
      "style": "TableText",
      "text": "human_variable:HV07"
    },
    {
      "anchor": "V82-P3718",
      "ordinal": 3718,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3719",
      "ordinal": 3719,
      "style": "TableText",
      "text": "反馈写回"
    },
    {
      "anchor": "V82-P3720",
      "ordinal": 3720,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3721",
      "ordinal": 3721,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3722",
      "ordinal": 3722,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3723",
      "ordinal": 3723,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3724",
      "ordinal": 3724,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3725",
      "ordinal": 3725,
      "style": "TableText",
      "text": "申诉、审计和反馈只有改变记录、规则、资源、角色、责任、记忆或停止条件时才构成人类制度写回。"
    },
    {
      "anchor": "V82-P3726",
      "ordinal": 3726,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3727",
      "ordinal": 3727,
      "style": "TableText",
      "text": "具有反馈、申诉、审计或治理程序的人类结构"
    },
    {
      "anchor": "V82-P3728",
      "ordinal": 3728,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3729",
      "ordinal": 3729,
      "style": "TableText",
      "text": "只有接收回执、表态或发布而无状态更新"
    },
    {
      "anchor": "V82-P3730",
      "ordinal": 3730,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3731",
      "ordinal": 3731,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3732",
      "ordinal": 3732,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3733",
      "ordinal": 3733,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3734",
      "ordinal": 3734,
      "style": "TableText",
      "text": "1. D2"
    },
    {
      "anchor": "V82-P3735",
      "ordinal": 3735,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3736",
      "ordinal": 3736,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P3737",
      "ordinal": 3737,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3738",
      "ordinal": 3738,
      "style": "TableText",
      "text": "1. H3"
    },
    {
      "anchor": "V82-P3739",
      "ordinal": 3739,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3740",
      "ordinal": 3740,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3741",
      "ordinal": 3741,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3742",
      "ordinal": 3742,
      "style": "TableText",
      "text": "1. route_id=HV07-R0-writeback-classification；"
    },
    {
      "anchor": "V82-P3743",
      "ordinal": 3743,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P3744",
      "ordinal": 3744,
      "style": "TableText",
      "text": "when=输入通道、回执、字段前后版本、执行记录、生效时间、持续时间及停止或回滚状态可分别检查。；"
    },
    {
      "anchor": "V82-P3745",
      "ordinal": 3745,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3746",
      "ordinal": 3746,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3747",
      "ordinal": 3747,
      "style": "TableText",
      "text": "allowed_conclusion=区分未提交、已提交、已受理、字段改变、已执行、持续或失效的写回状态。；"
    },
    {
      "anchor": "V82-P3748",
      "ordinal": 3748,
      "style": "TableText",
      "text": "result_ceiling=只有字段改变且实际执行才称制度性写回；一次写回不称学习。"
    },
    {
      "anchor": "V82-P3749",
      "ordinal": 3749,
      "style": "TableText",
      "text": "2. route_id=HV07-R1-causal-feedback；"
    },
    {
      "anchor": "V82-P3750",
      "ordinal": 3750,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P3751",
      "ordinal": 3751,
      "style": "TableText",
      "text": "when=符合资格的G2-instance显示制度返回通道相对无返回或阻断条件改变预选后续状态或转移。；"
    },
    {
      "anchor": "V82-P3752",
      "ordinal": 3752,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance；"
    },
    {
      "anchor": "V82-P3753",
      "ordinal": 3753,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3754",
      "ordinal": 3754,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定字段、通道和窗口内的有效反馈与制度写回效应。；"
    },
    {
      "anchor": "V82-P3755",
      "ordinal": 3755,
      "style": "TableText",
      "text": "result_ceiling=不得从反馈存在推出学习、长期修复、正当性或授权扩大。"
    },
    {
      "anchor": "V82-P3756",
      "ordinal": 3756,
      "style": "TableText",
      "text": "3. route_id=HV07-R2-feedback-mediated-learning；"
    },
    {
      "anchor": "V82-P3757",
      "ordinal": 3757,
      "style": "TableText",
      "text": "claim_level=intertemporal_explanation；"
    },
    {
      "anchor": "V82-P3758",
      "ordinal": 3758,
      "style": "TableText",
      "text": "when=有效反馈已有G2-instance支持，且G3-instance显示可保留更新在重复轮次对预定任务提供历史条件增量。；"
    },
    {
      "anchor": "V82-P3759",
      "ordinal": 3759,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance、G3-instance；"
    },
    {
      "anchor": "V82-P3760",
      "ordinal": 3760,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3761",
      "ordinal": 3761,
      "style": "TableText",
      "text": "allowed_conclusion=登记限定任务、轮次和窗口内的反馈介导学习候选。；"
    },
    {
      "anchor": "V82-P3762",
      "ordinal": 3762,
      "style": "TableText",
      "text": "result_ceiling=不得称整体制度已经学习、修复完成或价值方向正确。"
    },
    {
      "anchor": "V82-P3763",
      "ordinal": 3763,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3764",
      "ordinal": 3764,
      "style": "TableText",
      "text": "1. 有效写回、阻塞写回与表面反馈"
    },
    {
      "anchor": "V82-P3765",
      "ordinal": 3765,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3766",
      "ordinal": 3766,
      "style": "TableText",
      "text": "1. 有渠道即会学习"
    },
    {
      "anchor": "V82-P3767",
      "ordinal": 3767,
      "style": "TableText",
      "text": "2. 一次更新即长期修复"
    },
    {
      "anchor": "V82-P3768",
      "ordinal": 3768,
      "style": "TableText",
      "text": "3. 沉默即同意"
    },
    {
      "anchor": "V82-P3769",
      "ordinal": 3769,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3770",
      "ordinal": 3770,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3771",
      "ordinal": 3771,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3772",
      "ordinal": 3772,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3773",
      "ordinal": 3773,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次反馈或申诉、写回个案、反馈总体、受理执行分布及聚合规则；X=空间范围：提交渠道、组织或平台边界、制度辖区与跨域申诉范围；T=时间跨度：提交、受理、字段变化、执行、持续与复核时滞；O=组织层级：反馈角色、受理团队、组织、制度至治理生态；C=因果层次：反馈事件、写回互动机制、中观程序结构、制度规则与系统条件；R=观察分辨率：原始反馈、处理序列、写回个案、结果分布、时效指标与摘要，并登记压缩损失；I=影响范围：直接申诉人与承接者、间接受影响者、二阶制度后果、跨域与代际影响；N=网络拓扑范围：反馈通道、受理节点、复核路径、阻塞点与跨层连接；J=管辖与授权范围：受理、字段修改、执行、停止、回滚与补救分别登记授权；登记跨层路径"
    },
    {
      "anchor": "V82-P3774",
      "ordinal": 3774,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3775",
      "ordinal": 3775,
      "style": "TableText",
      "text": "改变后续制度状态或转移的返回通道"
    },
    {
      "anchor": "V82-P3776",
      "ordinal": 3776,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3777",
      "ordinal": 3777,
      "style": "TableText",
      "text": "1. 反馈来源、通道、写回字段和后续变化"
    },
    {
      "anchor": "V82-P3778",
      "ordinal": 3778,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3779",
      "ordinal": 3779,
      "style": "TableText",
      "text": "1. 反馈代表性"
    },
    {
      "anchor": "V82-P3780",
      "ordinal": 3780,
      "style": "TableText",
      "text": "2. 跨层写回路径"
    },
    {
      "anchor": "V82-P3781",
      "ordinal": 3781,
      "style": "TableText",
      "text": "3. 聚合损失"
    },
    {
      "anchor": "V82-P3782",
      "ordinal": 3782,
      "style": "TableText",
      "text": "4. 外部复核"
    },
    {
      "anchor": "V82-P3783",
      "ordinal": 3783,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3784",
      "ordinal": 3784,
      "style": "TableText",
      "text": "1. 写回载体、时滞和责任主体可改变"
    },
    {
      "anchor": "V82-P3785",
      "ordinal": 3785,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3786",
      "ordinal": 3786,
      "style": "TableText",
      "text": "1. 无记录、规则、资源、角色或停止条件的过程"
    },
    {
      "anchor": "V82-P3787",
      "ordinal": 3787,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3788",
      "ordinal": 3788,
      "style": "TableText",
      "text": "1. 个案反馈直接代表总体意见"
    },
    {
      "anchor": "V82-P3789",
      "ordinal": 3789,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3790",
      "ordinal": 3790,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3791",
      "ordinal": 3791,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3792",
      "ordinal": 3792,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3793",
      "ordinal": 3793,
      "style": "TableText",
      "text": "1. 到达"
    },
    {
      "anchor": "V82-P3794",
      "ordinal": 3794,
      "style": "TableText",
      "text": "2. 受理"
    },
    {
      "anchor": "V82-P3795",
      "ordinal": 3795,
      "style": "TableText",
      "text": "3. 写回"
    },
    {
      "anchor": "V82-P3796",
      "ordinal": 3796,
      "style": "TableText",
      "text": "4. 阻塞"
    },
    {
      "anchor": "V82-P3797",
      "ordinal": 3797,
      "style": "TableText",
      "text": "5. 失真"
    },
    {
      "anchor": "V82-P3798",
      "ordinal": 3798,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3799",
      "ordinal": 3799,
      "style": "TableText",
      "text": "1. 反馈或申诉的提交与受理凭证"
    },
    {
      "anchor": "V82-P3800",
      "ordinal": 3800,
      "style": "TableText",
      "text": "2. 记录、规则、资源、角色、责任或停止条件的版本差异"
    },
    {
      "anchor": "V82-P3801",
      "ordinal": 3801,
      "style": "TableText",
      "text": "3. 变更的执行记录、生效时间与持续时间"
    },
    {
      "anchor": "V82-P3802",
      "ordinal": 3802,
      "style": "TableText",
      "text": "4. 复核、撤销、补救及后续状态变化"
    },
    {
      "anchor": "V82-P3803",
      "ordinal": 3803,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3804",
      "ordinal": 3804,
      "style": "TableText",
      "text": "1. 反馈原文"
    },
    {
      "anchor": "V82-P3805",
      "ordinal": 3805,
      "style": "TableText",
      "text": "2. 受理轨迹"
    },
    {
      "anchor": "V82-P3806",
      "ordinal": 3806,
      "style": "TableText",
      "text": "3. 字段版本"
    },
    {
      "anchor": "V82-P3807",
      "ordinal": 3807,
      "style": "TableText",
      "text": "4. 后续规则或资源变化"
    },
    {
      "anchor": "V82-P3808",
      "ordinal": 3808,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3809",
      "ordinal": 3809,
      "style": "TableText",
      "text": "1. 反馈来源"
    },
    {
      "anchor": "V82-P3810",
      "ordinal": 3810,
      "style": "TableText",
      "text": "2. 安全通道"
    },
    {
      "anchor": "V82-P3811",
      "ordinal": 3811,
      "style": "TableText",
      "text": "3. 责任人"
    },
    {
      "anchor": "V82-P3812",
      "ordinal": 3812,
      "style": "TableText",
      "text": "4. 复核程序"
    },
    {
      "anchor": "V82-P3813",
      "ordinal": 3813,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3814",
      "ordinal": 3814,
      "style": "TableText",
      "text": "1. 记录、规则、资源、角色、责任、记忆或停止条件更新"
    },
    {
      "anchor": "V82-P3815",
      "ordinal": 3815,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3816",
      "ordinal": 3816,
      "style": "TableText",
      "text": "登记提交、受理、决定、执行和复审时限"
    },
    {
      "anchor": "V82-P3817",
      "ordinal": 3817,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3818",
      "ordinal": 3818,
      "style": "TableText",
      "text": "记录未达反馈、保护性匿名与不可见处理"
    },
    {
      "anchor": "V82-P3819",
      "ordinal": 3819,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3820",
      "ordinal": 3820,
      "style": "TableText",
      "text": "无法安全提交、受反报复威胁或无数字接入的位置"
    },
    {
      "anchor": "V82-P3821",
      "ordinal": 3821,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3822",
      "ordinal": 3822,
      "style": "TableText",
      "text": "1. 提交者"
    },
    {
      "anchor": "V82-P3823",
      "ordinal": 3823,
      "style": "TableText",
      "text": "2. 被评价者"
    },
    {
      "anchor": "V82-P3824",
      "ordinal": 3824,
      "style": "TableText",
      "text": "3. 执行者"
    },
    {
      "anchor": "V82-P3825",
      "ordinal": 3825,
      "style": "TableText",
      "text": "4. 制度受益者"
    },
    {
      "anchor": "V82-P3826",
      "ordinal": 3826,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3827",
      "ordinal": 3827,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3828",
      "ordinal": 3828,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3829",
      "ordinal": 3829,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3830",
      "ordinal": 3830,
      "style": "TableText",
      "text": "1. 申诉系统"
    },
    {
      "anchor": "V82-P3831",
      "ordinal": 3831,
      "style": "TableText",
      "text": "2. 审计程序"
    },
    {
      "anchor": "V82-P3832",
      "ordinal": 3832,
      "style": "TableText",
      "text": "3. 会议记录"
    },
    {
      "anchor": "V82-P3833",
      "ordinal": 3833,
      "style": "TableText",
      "text": "4. 规则库"
    },
    {
      "anchor": "V82-P3834",
      "ordinal": 3834,
      "style": "TableText",
      "text": "5. 责任链"
    },
    {
      "anchor": "V82-P3835",
      "ordinal": 3835,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3836",
      "ordinal": 3836,
      "style": "TableText",
      "text": "1. 受理者"
    },
    {
      "anchor": "V82-P3837",
      "ordinal": 3837,
      "style": "TableText",
      "text": "2. 决策者"
    },
    {
      "anchor": "V82-P3838",
      "ordinal": 3838,
      "style": "TableText",
      "text": "3. 写回执行者"
    },
    {
      "anchor": "V82-P3839",
      "ordinal": 3839,
      "style": "TableText",
      "text": "4. 监督者"
    },
    {
      "anchor": "V82-P3840",
      "ordinal": 3840,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3841",
      "ordinal": 3841,
      "style": "TableText",
      "text": "反馈有效性与反馈内容正当性分别判断"
    },
    {
      "anchor": "V82-P3842",
      "ordinal": 3842,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3843",
      "ordinal": 3843,
      "style": "TableText",
      "text": "确认写回字段和后续变化时至解释级"
    },
    {
      "anchor": "V82-P3844",
      "ordinal": 3844,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3845",
      "ordinal": 3845,
      "style": "TableText",
      "text": "本变量只生成受理、字段变化、执行、持续时间与写回缺口描述，以及复核或程序修复需求，不授权改写记录规则、执行修复或关闭申诉；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3846",
      "ordinal": 3846,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3847",
      "ordinal": 3847,
      "style": "TableText",
      "text": "1. 申诉获得接收回执但记录、规则、资源和停止条件均未改变"
    },
    {
      "anchor": "V82-P3848",
      "ordinal": 3848,
      "style": "TableText",
      "text": "2. 审计报告被发布却没有责任人、时限或后续状态更新"
    },
    {
      "anchor": "V82-P3849",
      "ordinal": 3849,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3850",
      "ordinal": 3850,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，反馈提交者可经安全可达、反报复通道要求状态、时限、责任人与写回结果，并触发与原受理、写回或决策链独立的复核"
    },
    {
      "anchor": "V82-P3851",
      "ordinal": 3851,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3852",
      "ordinal": 3852,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误更新，实际恢复先前记录、规则、资源、角色或停止条件状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3853",
      "ordinal": 3853,
      "style": "SecH2",
      "text": "A.8　HV08 条件势场（完整接口卡）"
    },
    {
      "anchor": "V82-P3854",
      "ordinal": 3854,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3855",
      "ordinal": 3855,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3856",
      "ordinal": 3856,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3857",
      "ordinal": 3857,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P3858",
      "ordinal": 3858,
      "style": "TableText",
      "text": "HV08"
    },
    {
      "anchor": "V82-P3859",
      "ordinal": 3859,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P3860",
      "ordinal": 3860,
      "style": "TableText",
      "text": "human_variable:HV08"
    },
    {
      "anchor": "V82-P3861",
      "ordinal": 3861,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P3862",
      "ordinal": 3862,
      "style": "TableText",
      "text": "条件势场"
    },
    {
      "anchor": "V82-P3863",
      "ordinal": 3863,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P3864",
      "ordinal": 3864,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P3865",
      "ordinal": 3865,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P3866",
      "ordinal": 3866,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P3867",
      "ordinal": 3867,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P3868",
      "ordinal": 3868,
      "style": "TableText",
      "text": "资源、制度、关系、权力、安全、指标、平台与历史条件只有通过可检测机制改变人类行动概率或约束时进入解释。"
    },
    {
      "anchor": "V82-P3869",
      "ordinal": 3869,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P3870",
      "ordinal": 3870,
      "style": "TableText",
      "text": "人类行动受情境、制度与权力位置影响的场景"
    },
    {
      "anchor": "V82-P3871",
      "ordinal": 3871,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P3872",
      "ordinal": 3872,
      "style": "TableText",
      "text": "势场被当作万能背景、意图主体或道德标签"
    },
    {
      "anchor": "V82-P3873",
      "ordinal": 3873,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P3874",
      "ordinal": 3874,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3875",
      "ordinal": 3875,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3876",
      "ordinal": 3876,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P3877",
      "ordinal": 3877,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3878",
      "ordinal": 3878,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P3879",
      "ordinal": 3879,
      "style": "TableText",
      "text": "1. E2"
    },
    {
      "anchor": "V82-P3880",
      "ordinal": 3880,
      "style": "TableText",
      "text": "2. EVIDENCE"
    },
    {
      "anchor": "V82-P3881",
      "ordinal": 3881,
      "style": "TableText",
      "text": "3. SOURCE"
    },
    {
      "anchor": "V82-P3882",
      "ordinal": 3882,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P3883",
      "ordinal": 3883,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3884",
      "ordinal": 3884,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P3885",
      "ordinal": 3885,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P3886",
      "ordinal": 3886,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P3887",
      "ordinal": 3887,
      "style": "TableText",
      "text": "1. route_id=HV08-R0-condition-inventory；"
    },
    {
      "anchor": "V82-P3888",
      "ordinal": 3888,
      "style": "TableText",
      "text": "claim_level=candidate_description；"
    },
    {
      "anchor": "V82-P3889",
      "ordinal": 3889,
      "style": "TableText",
      "text": "when=资源、规则、位置、安全、指标、平台、AI中介或历史沉积可按位置、尺度和时间窗列出，但尚无符合资格的H4-instance。；"
    },
    {
      "anchor": "V82-P3890",
      "ordinal": 3890,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3891",
      "ordinal": 3891,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P3892",
      "ordinal": 3892,
      "style": "TableText",
      "text": "allowed_conclusion=登记候选条件、位置异质性、观察盲区、竞争解释与补证需求。；"
    },
    {
      "anchor": "V82-P3893",
      "ordinal": 3893,
      "style": "TableText",
      "text": "result_ceiling=仅称条件清单或候选通道；不得把条件人格化，也不得称权力、中介或反身效应已成立。"
    },
    {
      "anchor": "V82-P3894",
      "ordinal": 3894,
      "style": "TableText",
      "text": "2. route_id=HV08-R1-position-or-mediation-effect；"
    },
    {
      "anchor": "V82-P3895",
      "ordinal": 3895,
      "style": "TableText",
      "text": "claim_level=conditional_effect；"
    },
    {
      "anchor": "V82-P3896",
      "ordinal": 3896,
      "style": "TableText",
      "text": "when=H4-instance在证据覆盖、表达安全或对象行为中唯一预选的成功判据取得supported。；"
    },
    {
      "anchor": "V82-P3897",
      "ordinal": 3897,
      "style": "TableText",
      "text": "additional_inferential_requires=H4-instance；"
    },
    {
      "anchor": "V82-P3898",
      "ordinal": 3898,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3899",
      "ordinal": 3899,
      "style": "TableText",
      "text": "allowed_conclusion=登记该实例位置、中介、结果家族和窗口内的遮蔽、放大或行为响应通道。；"
    },
    {
      "anchor": "V82-P3900",
      "ordinal": 3900,
      "style": "TableText",
      "text": "result_ceiling=不外推到未选结果家族，不从位置或中介效应推出恶意、责任或自动处置。"
    },
    {
      "anchor": "V82-P3901",
      "ordinal": 3901,
      "style": "TableText",
      "text": "3. route_id=HV08-R2-reflexive-response；"
    },
    {
      "anchor": "V82-P3902",
      "ordinal": 3902,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P3903",
      "ordinal": 3903,
      "style": "TableText",
      "text": "when=H4-instance唯一预选反身响应判据，且观测、命名、评分或发布经实际通道到达对象并取得supported。；"
    },
    {
      "anchor": "V82-P3904",
      "ordinal": 3904,
      "style": "TableText",
      "text": "additional_inferential_requires=H4-instance；"
    },
    {
      "anchor": "V82-P3905",
      "ordinal": 3905,
      "style": "TableText",
      "text": "additional_protocol_requires=E3、CAUSAL、E4；"
    },
    {
      "anchor": "V82-P3906",
      "ordinal": 3906,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定观测或发布通道与窗口内的反身响应。；"
    },
    {
      "anchor": "V82-P3907",
      "ordinal": 3907,
      "style": "TableText",
      "text": "result_ceiling=一次响应不称持久反身性；不得据此隐藏观察、压制表达或扩大授权。"
    },
    {
      "anchor": "V82-P3908",
      "ordinal": 3908,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P3909",
      "ordinal": 3909,
      "style": "TableText",
      "text": "1. 条件性机会、约束、遮蔽与放大"
    },
    {
      "anchor": "V82-P3910",
      "ordinal": 3910,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P3911",
      "ordinal": 3911,
      "style": "TableText",
      "text": "1. 条件决定个体行为"
    },
    {
      "anchor": "V82-P3912",
      "ordinal": 3912,
      "style": "TableText",
      "text": "2. 权力位置证明恶意"
    },
    {
      "anchor": "V82-P3913",
      "ordinal": 3913,
      "style": "TableText",
      "text": "3. 环境具有意图"
    },
    {
      "anchor": "V82-P3914",
      "ordinal": 3914,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P3915",
      "ordinal": 3915,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3916",
      "ordinal": 3916,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3917",
      "ordinal": 3917,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P3918",
      "ordinal": 3918,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次暴露或评价事件、位置个案、受条件总体、响应分布及聚合规则；X=空间范围：互动现场、组织或平台边界、公开数字空间与跨域环境；T=时间跨度：暴露积累、响应、反身变化与消退窗口；O=组织层级：行动与评价角色、团队、组织、制度至治理生态；C=因果层次：暴露事件、条件—行为互动机制、中观权力结构、制度规则与系统条件；R=观察分辨率：原始暴露表达行为、时间序列、位置个案、响应分布、平台指标与摘要，并登记压缩损失；I=影响范围：直接被评价者、间接受影响者、二阶反身后果、跨域与代际影响；N=网络拓扑范围：权力与信息连接、中介节点、遮蔽区、放大路径与跨域传播；J=管辖与授权范围：规则配置、指标使用、公开评价、人工复核与处置分别登记授权；比较位置异质性"
    },
    {
      "anchor": "V82-P3919",
      "ordinal": 3919,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P3920",
      "ordinal": 3920,
      "style": "TableText",
      "text": "经实际通道改变行动概率、表达安全或证据分布的条件集合"
    },
    {
      "anchor": "V82-P3921",
      "ordinal": 3921,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P3922",
      "ordinal": 3922,
      "style": "TableText",
      "text": "1. 条件到行为或证据的机制链"
    },
    {
      "anchor": "V82-P3923",
      "ordinal": 3923,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P3924",
      "ordinal": 3924,
      "style": "TableText",
      "text": "1. 位置分布"
    },
    {
      "anchor": "V82-P3925",
      "ordinal": 3925,
      "style": "TableText",
      "text": "2. 条件异质性"
    },
    {
      "anchor": "V82-P3926",
      "ordinal": 3926,
      "style": "TableText",
      "text": "3. 跨域外部性"
    },
    {
      "anchor": "V82-P3927",
      "ordinal": 3927,
      "style": "TableText",
      "text": "4. J轴"
    },
    {
      "anchor": "V82-P3928",
      "ordinal": 3928,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P3929",
      "ordinal": 3929,
      "style": "TableText",
      "text": "1. 关键条件与作用强度可随尺度改变"
    },
    {
      "anchor": "V82-P3930",
      "ordinal": 3930,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P3931",
      "ordinal": 3931,
      "style": "TableText",
      "text": "1. 无意向行动、权力或制度位置的非人系统"
    },
    {
      "anchor": "V82-P3932",
      "ordinal": 3932,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P3933",
      "ordinal": 3933,
      "style": "TableText",
      "text": "1. 局部条件直接普遍化为所有主体的动机"
    },
    {
      "anchor": "V82-P3934",
      "ordinal": 3934,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P3935",
      "ordinal": 3935,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3936",
      "ordinal": 3936,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3937",
      "ordinal": 3937,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P3938",
      "ordinal": 3938,
      "style": "TableText",
      "text": "1. 支持"
    },
    {
      "anchor": "V82-P3939",
      "ordinal": 3939,
      "style": "TableText",
      "text": "2. 约束"
    },
    {
      "anchor": "V82-P3940",
      "ordinal": 3940,
      "style": "TableText",
      "text": "3. 遮蔽"
    },
    {
      "anchor": "V82-P3941",
      "ordinal": 3941,
      "style": "TableText",
      "text": "4. 放大"
    },
    {
      "anchor": "V82-P3942",
      "ordinal": 3942,
      "style": "TableText",
      "text": "5. 混合"
    },
    {
      "anchor": "V82-P3943",
      "ordinal": 3943,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P3944",
      "ordinal": 3944,
      "style": "TableText",
      "text": "1. 资源、规则、平台或公开条件改变前后的行为差异"
    },
    {
      "anchor": "V82-P3945",
      "ordinal": 3945,
      "style": "TableText",
      "text": "2. 不同位置的表达安全、证据覆盖和缺席率"
    },
    {
      "anchor": "V82-P3946",
      "ordinal": 3946,
      "style": "TableText",
      "text": "3. 指标、评分或AI中介前后的可见性与处置变化"
    },
    {
      "anchor": "V82-P3947",
      "ordinal": 3947,
      "style": "TableText",
      "text": "4. 比较条件下候选通道效应是否超过预定阈值"
    },
    {
      "anchor": "V82-P3948",
      "ordinal": 3948,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P3949",
      "ordinal": 3949,
      "style": "TableText",
      "text": "1. 资源与规则"
    },
    {
      "anchor": "V82-P3950",
      "ordinal": 3950,
      "style": "TableText",
      "text": "2. 位置差异"
    },
    {
      "anchor": "V82-P3951",
      "ordinal": 3951,
      "style": "TableText",
      "text": "3. 平台或指标变化"
    },
    {
      "anchor": "V82-P3952",
      "ordinal": 3952,
      "style": "TableText",
      "text": "4. 行为响应"
    },
    {
      "anchor": "V82-P3953",
      "ordinal": 3953,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P3954",
      "ordinal": 3954,
      "style": "TableText",
      "text": "1. 边界与接口2. 观察位置3. 因果合同"
    },
    {
      "anchor": "V82-P3955",
      "ordinal": 3955,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P3956",
      "ordinal": 3956,
      "style": "TableText",
      "text": "1. 可行路径2. 表达和证据3. 生成与失稳"
    },
    {
      "anchor": "V82-P3957",
      "ordinal": 3957,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P3958",
      "ordinal": 3958,
      "style": "TableText",
      "text": "登记条件积累、响应与消退时滞"
    },
    {
      "anchor": "V82-P3959",
      "ordinal": 3959,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P3960",
      "ordinal": 3960,
      "style": "TableText",
      "text": "记录不可观察条件、共线性和反身变化"
    },
    {
      "anchor": "V82-P3961",
      "ordinal": 3961,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P3962",
      "ordinal": 3962,
      "style": "TableText",
      "text": "因安全、身份或平台门槛而不可见的位置"
    },
    {
      "anchor": "V82-P3963",
      "ordinal": 3963,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P3964",
      "ordinal": 3964,
      "style": "TableText",
      "text": "1. 优势位置"
    },
    {
      "anchor": "V82-P3965",
      "ordinal": 3965,
      "style": "TableText",
      "text": "2. 低权力位置"
    },
    {
      "anchor": "V82-P3966",
      "ordinal": 3966,
      "style": "TableText",
      "text": "3. 中介者"
    },
    {
      "anchor": "V82-P3967",
      "ordinal": 3967,
      "style": "TableText",
      "text": "4. 被评价者"
    },
    {
      "anchor": "V82-P3968",
      "ordinal": 3968,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P3969",
      "ordinal": 3969,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3970",
      "ordinal": 3970,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P3971",
      "ordinal": 3971,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P3972",
      "ordinal": 3972,
      "style": "TableText",
      "text": "1. 制度"
    },
    {
      "anchor": "V82-P3973",
      "ordinal": 3973,
      "style": "TableText",
      "text": "2. 资源配置"
    },
    {
      "anchor": "V82-P3974",
      "ordinal": 3974,
      "style": "TableText",
      "text": "3. 平台"
    },
    {
      "anchor": "V82-P3975",
      "ordinal": 3975,
      "style": "TableText",
      "text": "4. 指标"
    },
    {
      "anchor": "V82-P3976",
      "ordinal": 3976,
      "style": "TableText",
      "text": "5. 关系网络"
    },
    {
      "anchor": "V82-P3977",
      "ordinal": 3977,
      "style": "TableText",
      "text": "6. 历史沉积"
    },
    {
      "anchor": "V82-P3978",
      "ordinal": 3978,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P3979",
      "ordinal": 3979,
      "style": "TableText",
      "text": "1. 规则制定者"
    },
    {
      "anchor": "V82-P3980",
      "ordinal": 3980,
      "style": "TableText",
      "text": "2. 平台运营者"
    },
    {
      "anchor": "V82-P3981",
      "ordinal": 3981,
      "style": "TableText",
      "text": "3. 资源配置者"
    },
    {
      "anchor": "V82-P3982",
      "ordinal": 3982,
      "style": "TableText",
      "text": "4. 行动决策者"
    },
    {
      "anchor": "V82-P3983",
      "ordinal": 3983,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P3984",
      "ordinal": 3984,
      "style": "TableText",
      "text": "条件优势或筛选结果不构成正当性"
    },
    {
      "anchor": "V82-P3985",
      "ordinal": 3985,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P3986",
      "ordinal": 3986,
      "style": "TableText",
      "text": "机制链与反事实充分时至解释级"
    },
    {
      "anchor": "V82-P3987",
      "ordinal": 3987,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P3988",
      "ordinal": 3988,
      "style": "TableText",
      "text": "本变量只生成候选条件通道、位置异质性、证据遮蔽与风险降低需求描述，不授权改变规则平台、资源配置、评价或处置主体；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P3989",
      "ordinal": 3989,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P3990",
      "ordinal": 3990,
      "style": "TableText",
      "text": "1. 相同制度条件下不同安全和权力位置出现相反行动"
    },
    {
      "anchor": "V82-P3991",
      "ordinal": 3991,
      "style": "TableText",
      "text": "2. 以权力或平台标签替代实际因果通道后无法解释状态变化"
    },
    {
      "anchor": "V82-P3992",
      "ordinal": 3992,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P3993",
      "ordinal": 3993,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，不同位置可经安全可达、反报复通道提交机制差异、缺席信号与安全影响，并触发与原势场判断或决策链独立的复核"
    },
    {
      "anchor": "V82-P3994",
      "ordinal": 3994,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P3995",
      "ordinal": 3995,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销不成立的势场归因、移除位置标签及其下游评价处置效力并恢复未决状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P3996",
      "ordinal": 3996,
      "style": "SecH2",
      "text": "A.9　HV09 结构负荷（完整接口卡）"
    },
    {
      "anchor": "V82-P3997",
      "ordinal": 3997,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P3998",
      "ordinal": 3998,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P3999",
      "ordinal": 3999,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4000",
      "ordinal": 4000,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P4001",
      "ordinal": 4001,
      "style": "TableText",
      "text": "HV09"
    },
    {
      "anchor": "V82-P4002",
      "ordinal": 4002,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P4003",
      "ordinal": 4003,
      "style": "TableText",
      "text": "human_variable:HV09"
    },
    {
      "anchor": "V82-P4004",
      "ordinal": 4004,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P4005",
      "ordinal": 4005,
      "style": "TableText",
      "text": "结构负荷"
    },
    {
      "anchor": "V82-P4006",
      "ordinal": 4006,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P4007",
      "ordinal": 4007,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P4008",
      "ordinal": 4008,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P4009",
      "ordinal": 4009,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P4010",
      "ordinal": 4010,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P4011",
      "ordinal": 4011,
      "style": "TableText",
      "text": "人类结构负荷必须把任务、协调损耗、维护要求、容量、恢复余量和成本承担位置共同登记。"
    },
    {
      "anchor": "V82-P4012",
      "ordinal": 4012,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P4013",
      "ordinal": 4013,
      "style": "TableText",
      "text": "持续运转、维护、照护或高压条件下的人类结构"
    },
    {
      "anchor": "V82-P4014",
      "ordinal": 4014,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P4015",
      "ordinal": 4015,
      "style": "TableText",
      "text": "只用熵、脆弱或韧性隐喻而无任务、容量和恢复机制"
    },
    {
      "anchor": "V82-P4016",
      "ordinal": 4016,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P4017",
      "ordinal": 4017,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4018",
      "ordinal": 4018,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4019",
      "ordinal": 4019,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P4020",
      "ordinal": 4020,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4021",
      "ordinal": 4021,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P4022",
      "ordinal": 4022,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P4023",
      "ordinal": 4023,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P4024",
      "ordinal": 4024,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4025",
      "ordinal": 4025,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P4026",
      "ordinal": 4026,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4027",
      "ordinal": 4027,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P4028",
      "ordinal": 4028,
      "style": "TableText",
      "text": "1. route_id=HV09-R0-instant-task-capacity；"
    },
    {
      "anchor": "V82-P4029",
      "ordinal": 4029,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P4030",
      "ordinal": 4030,
      "style": "TableText",
      "text": "when=同一窗口、位置与类型映射下的任务或协调要求、容量、恢复余量及其分布可观察。；"
    },
    {
      "anchor": "V82-P4031",
      "ordinal": 4031,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4032",
      "ordinal": 4032,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4033",
      "ordinal": 4033,
      "style": "TableText",
      "text": "allowed_conclusion=登记瞬时任务—容量关系、余量、积压、局部缺口与恢复状态。；"
    },
    {
      "anchor": "V82-P4034",
      "ordinal": 4034,
      "style": "TableText",
      "text": "result_ceiling=只到同窗描述；瞬时峰值或缺口不自动成为过载机制、累积损伤或崩溃。"
    },
    {
      "anchor": "V82-P4035",
      "ordinal": 4035,
      "style": "TableText",
      "text": "2. route_id=HV09-R1-overload-mechanism；"
    },
    {
      "anchor": "V82-P4036",
      "ordinal": 4036,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P4037",
      "ordinal": 4037,
      "style": "TableText",
      "text": "when=CM-LOAD的适用条件完整，且符合资格的G2-instance显示负荷、补给、减载或恢复通道对预选结果有超过阈值效应。；"
    },
    {
      "anchor": "V82-P4038",
      "ordinal": 4038,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance、CM-LOAD；"
    },
    {
      "anchor": "V82-P4039",
      "ordinal": 4039,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P4040",
      "ordinal": 4040,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定位置、类型、窗口和通道内的过载或恢复机制候选。；"
    },
    {
      "anchor": "V82-P4041",
      "ordinal": 4041,
      "style": "TableText",
      "text": "result_ceiling=不得普遍化为熵、韧性或所有位置必然崩溃，也不直接生成减载或牺牲义务。"
    },
    {
      "anchor": "V82-P4042",
      "ordinal": 4042,
      "style": "TableText",
      "text": "3. route_id=HV09-R2-cumulative-overload；"
    },
    {
      "anchor": "V82-P4043",
      "ordinal": 4043,
      "style": "TableText",
      "text": "claim_level=intertemporal_explanation；"
    },
    {
      "anchor": "V82-P4044",
      "ordinal": 4044,
      "style": "TableText",
      "text": "when=过载机制已有G2-instance与CM-LOAD支持，且G3-instance显示历史负荷对后续容量、错误或恢复具有条件增量。；"
    },
    {
      "anchor": "V82-P4045",
      "ordinal": 4045,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance、CM-LOAD、G3-instance；"
    },
    {
      "anchor": "V82-P4046",
      "ordinal": 4046,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P4047",
      "ordinal": 4047,
      "style": "TableText",
      "text": "allowed_conclusion=登记预注册载体、窗口和结果内的累积损伤或迟恢复候选。；"
    },
    {
      "anchor": "V82-P4048",
      "ordinal": 4048,
      "style": "TableText",
      "text": "result_ceiling=不推出不可逆、必然崩溃、责任归属或具名主体承担义务。"
    },
    {
      "anchor": "V82-P4049",
      "ordinal": 4049,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P4050",
      "ordinal": 4050,
      "style": "TableText",
      "text": "1. 候选过载、余量不足、维护缺口与恢复差异"
    },
    {
      "anchor": "V82-P4051",
      "ordinal": 4051,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P4052",
      "ordinal": 4052,
      "style": "TableText",
      "text": "1. 承接者应继续承担"
    },
    {
      "anchor": "V82-P4053",
      "ordinal": 4053,
      "style": "TableText",
      "text": "2. 高负荷证明奉献"
    },
    {
      "anchor": "V82-P4054",
      "ordinal": 4054,
      "style": "TableText",
      "text": "3. 过载主体等于失稳机制"
    },
    {
      "anchor": "V82-P4055",
      "ordinal": 4055,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P4056",
      "ordinal": 4056,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4057",
      "ordinal": 4057,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4058",
      "ordinal": 4058,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P4059",
      "ordinal": 4059,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务负荷、承接个案、岗位或群体总体、负荷容量分布及聚合规则；X=空间范围：工作或照护现场、组织边界、数字劳动空间与跨域外包范围；T=时间跨度：瞬时峰值、持续积压、恢复时滞、跨期与代际窗口；O=组织层级：承接角色、团队、组织、制度至治理生态；C=因果层次：任务事件、任务—容量互动机制、中观瓶颈结构、制度分配与系统条件；R=观察分辨率：原始任务工时记录、负荷序列、承接个案、容量分布、时延错误指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接替代者、二阶外溢、跨域与代际成本；N=网络拓扑范围：任务依赖、关键瓶颈、替代节点、恢复路径与跨域外包网络；J=管辖与授权范围：任务分配、资源调整、停止、绩效使用与补救分别登记授权；保留负荷容量分布"
    },
    {
      "anchor": "V82-P4060",
      "ordinal": 4060,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P4061",
      "ordinal": 4061,
      "style": "TableText",
      "text": "给定窗口内任务和协调要求相对可用容量与恢复余量的结构关系"
    },
    {
      "anchor": "V82-P4062",
      "ordinal": 4062,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P4063",
      "ordinal": 4063,
      "style": "TableText",
      "text": "1. 负荷、容量、恢复与成本位置"
    },
    {
      "anchor": "V82-P4064",
      "ordinal": 4064,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P4065",
      "ordinal": 4065,
      "style": "TableText",
      "text": "1. 负荷分布"
    },
    {
      "anchor": "V82-P4066",
      "ordinal": 4066,
      "style": "TableText",
      "text": "2. 聚合遮蔽"
    },
    {
      "anchor": "V82-P4067",
      "ordinal": 4067,
      "style": "TableText",
      "text": "3. 责任继承"
    },
    {
      "anchor": "V82-P4068",
      "ordinal": 4068,
      "style": "TableText",
      "text": "4. 代际影响"
    },
    {
      "anchor": "V82-P4069",
      "ordinal": 4069,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P4070",
      "ordinal": 4070,
      "style": "TableText",
      "text": "1. 瓶颈、容量和恢复方式可随层级改变"
    },
    {
      "anchor": "V82-P4071",
      "ordinal": 4071,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P4072",
      "ordinal": 4072,
      "style": "TableText",
      "text": "1. 无持续非平衡、维护或人类承接要求的过程"
    },
    {
      "anchor": "V82-P4073",
      "ordinal": 4073,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P4074",
      "ordinal": 4074,
      "style": "TableText",
      "text": "1. 平均负荷掩盖局部过载"
    },
    {
      "anchor": "V82-P4075",
      "ordinal": 4075,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P4076",
      "ordinal": 4076,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4077",
      "ordinal": 4077,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4078",
      "ordinal": 4078,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P4079",
      "ordinal": 4079,
      "style": "TableText",
      "text": "1. 低负荷"
    },
    {
      "anchor": "V82-P4080",
      "ordinal": 4080,
      "style": "TableText",
      "text": "2. 可承受"
    },
    {
      "anchor": "V82-P4081",
      "ordinal": 4081,
      "style": "TableText",
      "text": "3. 临界"
    },
    {
      "anchor": "V82-P4082",
      "ordinal": 4082,
      "style": "TableText",
      "text": "4. 过载"
    },
    {
      "anchor": "V82-P4083",
      "ordinal": 4083,
      "style": "TableText",
      "text": "5. 恢复"
    },
    {
      "anchor": "V82-P4084",
      "ordinal": 4084,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P4085",
      "ordinal": 4085,
      "style": "TableText",
      "text": "1. 单位时间任务量、积压、时延和错误率"
    },
    {
      "anchor": "V82-P4086",
      "ordinal": 4086,
      "style": "TableText",
      "text": "2. 人员资源容量、隐性劳动与替代可用性"
    },
    {
      "anchor": "V82-P4087",
      "ordinal": 4087,
      "style": "TableText",
      "text": "3. 停止、缺席、退出和恢复曲线"
    },
    {
      "anchor": "V82-P4088",
      "ordinal": 4088,
      "style": "TableText",
      "text": "4. 平均负荷与关键局部承接位置的分布差异"
    },
    {
      "anchor": "V82-P4089",
      "ordinal": 4089,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P4090",
      "ordinal": 4090,
      "style": "TableText",
      "text": "1. 任务量"
    },
    {
      "anchor": "V82-P4091",
      "ordinal": 4091,
      "style": "TableText",
      "text": "2. 时延与错误"
    },
    {
      "anchor": "V82-P4092",
      "ordinal": 4092,
      "style": "TableText",
      "text": "3. 人员与资源"
    },
    {
      "anchor": "V82-P4093",
      "ordinal": 4093,
      "style": "TableText",
      "text": "4. 恢复记录"
    },
    {
      "anchor": "V82-P4094",
      "ordinal": 4094,
      "style": "TableText",
      "text": "5. 退出和缺席"
    },
    {
      "anchor": "V82-P4095",
      "ordinal": 4095,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P4096",
      "ordinal": 4096,
      "style": "TableText",
      "text": "1. 承接层"
    },
    {
      "anchor": "V82-P4097",
      "ordinal": 4097,
      "style": "TableText",
      "text": "2. 动力—承接链"
    },
    {
      "anchor": "V82-P4098",
      "ordinal": 4098,
      "style": "TableText",
      "text": "3. 条件势场"
    },
    {
      "anchor": "V82-P4099",
      "ordinal": 4099,
      "style": "TableText",
      "text": "4. 瞬时负荷只调用G2与CM-LOAD；累积损伤、迟恢复或历史条件增量另需预注册G3-instance，H5候选留痕不能替代G3"
    },
    {
      "anchor": "V82-P4100",
      "ordinal": 4100,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P4101",
      "ordinal": 4101,
      "style": "TableText",
      "text": "1. 状态更新2. 失稳行为3. 维护和修复需求"
    },
    {
      "anchor": "V82-P4102",
      "ordinal": 4102,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P4103",
      "ordinal": 4103,
      "style": "TableText",
      "text": "区分即时峰值、持续积压、恢复时滞与代际成本"
    },
    {
      "anchor": "V82-P4104",
      "ordinal": 4104,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P4105",
      "ordinal": 4105,
      "style": "TableText",
      "text": "记录隐性劳动、外包成本和保护性缺席"
    },
    {
      "anchor": "V82-P4106",
      "ordinal": 4106,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P4107",
      "ordinal": 4107,
      "style": "TableText",
      "text": "非正式劳动、家庭照护、外包和低可见承接位置"
    },
    {
      "anchor": "V82-P4108",
      "ordinal": 4108,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P4109",
      "ordinal": 4109,
      "style": "TableText",
      "text": "1. 承接者"
    },
    {
      "anchor": "V82-P4110",
      "ordinal": 4110,
      "style": "TableText",
      "text": "2. 依赖服务者"
    },
    {
      "anchor": "V82-P4111",
      "ordinal": 4111,
      "style": "TableText",
      "text": "3. 替代者"
    },
    {
      "anchor": "V82-P4112",
      "ordinal": 4112,
      "style": "TableText",
      "text": "4. 成本外溢位置"
    },
    {
      "anchor": "V82-P4113",
      "ordinal": 4113,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P4114",
      "ordinal": 4114,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4115",
      "ordinal": 4115,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4116",
      "ordinal": 4116,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P4117",
      "ordinal": 4117,
      "style": "TableText",
      "text": "1. 人员"
    },
    {
      "anchor": "V82-P4118",
      "ordinal": 4118,
      "style": "TableText",
      "text": "2. 岗位"
    },
    {
      "anchor": "V82-P4119",
      "ordinal": 4119,
      "style": "TableText",
      "text": "3. 程序"
    },
    {
      "anchor": "V82-P4120",
      "ordinal": 4120,
      "style": "TableText",
      "text": "4. 设施"
    },
    {
      "anchor": "V82-P4121",
      "ordinal": 4121,
      "style": "TableText",
      "text": "5. 预算"
    },
    {
      "anchor": "V82-P4122",
      "ordinal": 4122,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P4123",
      "ordinal": 4123,
      "style": "TableText",
      "text": "1. 任务分配者"
    },
    {
      "anchor": "V82-P4124",
      "ordinal": 4124,
      "style": "TableText",
      "text": "2. 资源配置者"
    },
    {
      "anchor": "V82-P4125",
      "ordinal": 4125,
      "style": "TableText",
      "text": "3. 授权者"
    },
    {
      "anchor": "V82-P4126",
      "ordinal": 4126,
      "style": "TableText",
      "text": "4. 监督者"
    },
    {
      "anchor": "V82-P4127",
      "ordinal": 4127,
      "style": "TableText",
      "text": "5. 补救责任者"
    },
    {
      "anchor": "V82-P4128",
      "ordinal": 4128,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P4129",
      "ordinal": 4129,
      "style": "TableText",
      "text": "高效率或高承载不构成正当性"
    },
    {
      "anchor": "V82-P4130",
      "ordinal": 4130,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P4131",
      "ordinal": 4131,
      "style": "TableText",
      "text": "负荷容量和恢复证据充分时至诊断级"
    },
    {
      "anchor": "V82-P4132",
      "ordinal": 4132,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P4133",
      "ordinal": 4133,
      "style": "TableText",
      "text": "本变量只生成负荷、容量、恢复、局部过载与减载补资源需求描述，不授权任务削减、资源投入、绩效处置或强迫承担；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P4134",
      "ordinal": 4134,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P4135",
      "ordinal": 4135,
      "style": "TableText",
      "text": "1. 总体平均容量充足但少数关键承接位置持续过载"
    },
    {
      "anchor": "V82-P4136",
      "ordinal": 4136,
      "style": "TableText",
      "text": "2. 只用熵或韧性隐喻却无法识别任务、容量和恢复通道"
    },
    {
      "anchor": "V82-P4137",
      "ordinal": 4137,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P4138",
      "ordinal": 4138,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，承接者可经安全可达、反报复通道报告隐性劳动、过载和恢复需求，并触发与原负荷判断、绩效或任务决策链独立的复核"
    },
    {
      "anchor": "V82-P4139",
      "ordinal": 4139,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P4140",
      "ordinal": 4140,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误负荷判断及绩效或责任效力，实际恢复任务、资源与记录状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P4141",
      "ordinal": 4141,
      "style": "SecH2",
      "text": "A.10　HV10 演化相位（完整接口卡）"
    },
    {
      "anchor": "V82-P4142",
      "ordinal": 4142,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P4143",
      "ordinal": 4143,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4144",
      "ordinal": 4144,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4145",
      "ordinal": 4145,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P4146",
      "ordinal": 4146,
      "style": "TableText",
      "text": "HV10"
    },
    {
      "anchor": "V82-P4147",
      "ordinal": 4147,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P4148",
      "ordinal": 4148,
      "style": "TableText",
      "text": "human_variable:HV10"
    },
    {
      "anchor": "V82-P4149",
      "ordinal": 4149,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P4150",
      "ordinal": 4150,
      "style": "TableText",
      "text": "演化相位"
    },
    {
      "anchor": "V82-P4151",
      "ordinal": 4151,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P4152",
      "ordinal": 4152,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P4153",
      "ordinal": 4153,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P4154",
      "ordinal": 4154,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P4155",
      "ordinal": 4155,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P4156",
      "ordinal": 4156,
      "style": "TableText",
      "text": "S0-S6和X0只适用于存在方向、生成主体或事件、承接层与制度化过程的人类意向性集体，且允许跳阶、并行、混合、回退、分裂、合并、休眠、吞并和功能转移。"
    },
    {
      "anchor": "V82-P4157",
      "ordinal": 4157,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P4158",
      "ordinal": 4158,
      "style": "TableText",
      "text": "符合适用条件的人类意向性集体"
    },
    {
      "anchor": "V82-P4159",
      "ordinal": 4159,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P4160",
      "ordinal": 4160,
      "style": "TableText",
      "text": "适用条件缺失、阶段被道德化或标题与判据不一致"
    },
    {
      "anchor": "V82-P4161",
      "ordinal": 4161,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P4162",
      "ordinal": 4162,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4163",
      "ordinal": 4163,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4164",
      "ordinal": 4164,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P4165",
      "ordinal": 4165,
      "style": "TableText",
      "text": "1. human_variable:HV03"
    },
    {
      "anchor": "V82-P4166",
      "ordinal": 4166,
      "style": "TableText",
      "text": "2. human_variable:HV04"
    },
    {
      "anchor": "V82-P4167",
      "ordinal": 4167,
      "style": "TableText",
      "text": "3. human_variable:HV05"
    },
    {
      "anchor": "V82-P4168",
      "ordinal": 4168,
      "style": "TableText",
      "text": "4. human_variable:HV07"
    },
    {
      "anchor": "V82-P4169",
      "ordinal": 4169,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P4170",
      "ordinal": 4170,
      "style": "TableText",
      "text": "1. EVIDENCE2. SOURCE"
    },
    {
      "anchor": "V82-P4171",
      "ordinal": 4171,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P4172",
      "ordinal": 4172,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4173",
      "ordinal": 4173,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P4174",
      "ordinal": 4174,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4175",
      "ordinal": 4175,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P4176",
      "ordinal": 4176,
      "style": "TableText",
      "text": "1. route_id=HV10-R0-component-applicability；"
    },
    {
      "anchor": "V82-P4177",
      "ordinal": 4177,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P4178",
      "ordinal": 4178,
      "style": "TableText",
      "text": "when=HV03、HV04、HV05与HV07已有可审计评估记录；记录允许为missing、not_applicable或unsupported，不要求四组件经验成立。；"
    },
    {
      "anchor": "V82-P4179",
      "ordinal": 4179,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4180",
      "ordinal": 4180,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4181",
      "ordinal": 4181,
      "style": "TableText",
      "text": "allowed_conclusion=登记适用、不适用、组件缺失、混合状态与继续观察需求。；"
    },
    {
      "anchor": "V82-P4182",
      "ordinal": 4182,
      "style": "TableText",
      "text": "result_ceiling=组件检查本身不产生S0-S6或X0相位匹配。"
    },
    {
      "anchor": "V82-P4183",
      "ordinal": 4183,
      "style": "TableText",
      "text": "2. route_id=HV10-R1-pattern-phase-match；"
    },
    {
      "anchor": "V82-P4184",
      "ordinal": 4184,
      "style": "TableText",
      "text": "claim_level=descriptive_classification；"
    },
    {
      "anchor": "V82-P4185",
      "ordinal": 4185,
      "style": "TableText",
      "text": "when=CM-PHASE的状态判据、观察窗、混合与转换规则完整，并在重复窗口匹配。；"
    },
    {
      "anchor": "V82-P4186",
      "ordinal": 4186,
      "style": "TableText",
      "text": "additional_inferential_requires=CM-PHASE；"
    },
    {
      "anchor": "V82-P4187",
      "ordinal": 4187,
      "style": "TableText",
      "text": "additional_protocol_requires=E4；"
    },
    {
      "anchor": "V82-P4188",
      "ordinal": 4188,
      "style": "TableText",
      "text": "allowed_conclusion=登记S0-S6或X0的原型匹配、混合、并行、回退、休眠或转换描述。；"
    },
    {
      "anchor": "V82-P4189",
      "ordinal": 4189,
      "style": "TableText",
      "text": "result_ceiling=只到模式相位；相位不是健康、成功、正当性或淘汰等级。"
    },
    {
      "anchor": "V82-P4190",
      "ordinal": 4190,
      "style": "TableText",
      "text": "3. route_id=HV10-R2-causal-transition；"
    },
    {
      "anchor": "V82-P4191",
      "ordinal": 4191,
      "style": "TableText",
      "text": "claim_level=mechanism_explanation；"
    },
    {
      "anchor": "V82-P4192",
      "ordinal": 4192,
      "style": "TableText",
      "text": "when=CM-PHASE匹配成立，且G2-instance识别指定相位转移通道对预选状态变化的效应。；"
    },
    {
      "anchor": "V82-P4193",
      "ordinal": 4193,
      "style": "TableText",
      "text": "additional_inferential_requires=CM-PHASE、G2-instance；"
    },
    {
      "anchor": "V82-P4194",
      "ordinal": 4194,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P4195",
      "ordinal": 4195,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定对象、窗口和通道内的候选因果相位转移。；"
    },
    {
      "anchor": "V82-P4196",
      "ordinal": 4196,
      "style": "TableText",
      "text": "result_ceiling=不得从转移机制推出必然阶段序列、价值方向或推进与淘汰授权。"
    },
    {
      "anchor": "V82-P4197",
      "ordinal": 4197,
      "style": "TableText",
      "text": "4. route_id=HV10-R3-path-dependent-phase；"
    },
    {
      "anchor": "V82-P4198",
      "ordinal": 4198,
      "style": "TableText",
      "text": "claim_level=intertemporal_explanation；"
    },
    {
      "anchor": "V82-P4199",
      "ordinal": 4199,
      "style": "TableText",
      "text": "when=CM-PHASE匹配成立，且G3-instance显示历史相位变量对后续状态、迟滞或回退具有条件增量。；"
    },
    {
      "anchor": "V82-P4200",
      "ordinal": 4200,
      "style": "TableText",
      "text": "additional_inferential_requires=CM-PHASE、G3-instance；"
    },
    {
      "anchor": "V82-P4201",
      "ordinal": 4201,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P4202",
      "ordinal": 4202,
      "style": "TableText",
      "text": "allowed_conclusion=登记预注册窗口内的路径依赖、迟滞或历史相位差异候选。；"
    },
    {
      "anchor": "V82-P4203",
      "ordinal": 4203,
      "style": "TableText",
      "text": "result_ceiling=不得称命运、绝对不可逆或自动规定修复、退出与退场方案。"
    },
    {
      "anchor": "V82-P4204",
      "ordinal": 4204,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P4205",
      "ordinal": 4205,
      "style": "TableText",
      "text": "1. 条件性状态坐标"
    },
    {
      "anchor": "V82-P4206",
      "ordinal": 4206,
      "style": "TableText",
      "text": "2. 非线性路径"
    },
    {
      "anchor": "V82-P4207",
      "ordinal": 4207,
      "style": "TableText",
      "text": "3. 有序退场X0"
    },
    {
      "anchor": "V82-P4208",
      "ordinal": 4208,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P4209",
      "ordinal": 4209,
      "style": "TableText",
      "text": "1. 所有系统必经S0-S6"
    },
    {
      "anchor": "V82-P4210",
      "ordinal": 4210,
      "style": "TableText",
      "text": "2. 阶段越高越正当"
    },
    {
      "anchor": "V82-P4211",
      "ordinal": 4211,
      "style": "TableText",
      "text": "3. 解体等于失败"
    },
    {
      "anchor": "V82-P4212",
      "ordinal": 4212,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P4213",
      "ordinal": 4213,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4214",
      "ordinal": 4214,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4215",
      "ordinal": 4215,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P4216",
      "ordinal": 4216,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次状态事件、局部群体个案、意向集体总体、相位分布及聚合规则；X=空间范围：行动现场、组织或制度边界、数字协作空间与跨域演化范围；T=时间跨度：状态窗口、转移时滞、回退、休眠、迟滞与代际周期；O=组织层级：成员角色、团队、组织、制度至治理生态；C=因果层次：状态事件、转移互动机制、中观相位结构、制度化过程与系统条件；R=观察分辨率：原始状态事件、转移序列、局部个案、相位分布、状态指标与摘要，并登记压缩损失；I=影响范围：直接成员与承接者、退出者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：局部相位簇群、跨层连接、分裂合并、功能转移与继承路径；J=管辖与授权范围：相位命名、监测采用、试探、推进、退场与淘汰分别登记授权；保留混合相位"
    },
    {
      "anchor": "V82-P4217",
      "ordinal": 4217,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P4218",
      "ordinal": 4218,
      "style": "TableText",
      "text": "具有人类意向、生成、承接和制度化的集体状态"
    },
    {
      "anchor": "V82-P4219",
      "ordinal": 4219,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P4220",
      "ordinal": 4220,
      "style": "TableText",
      "text": "1. 适用条件"
    },
    {
      "anchor": "V82-P4221",
      "ordinal": 4221,
      "style": "TableText",
      "text": "2. 相位判据"
    },
    {
      "anchor": "V82-P4222",
      "ordinal": 4222,
      "style": "TableText",
      "text": "3. 非线性路径"
    },
    {
      "anchor": "V82-P4223",
      "ordinal": 4223,
      "style": "TableText",
      "text": "4. X0不计为第八阶段"
    },
    {
      "anchor": "V82-P4224",
      "ordinal": 4224,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P4225",
      "ordinal": 4225,
      "style": "TableText",
      "text": "1. 局部相位分布"
    },
    {
      "anchor": "V82-P4226",
      "ordinal": 4226,
      "style": "TableText",
      "text": "2. 跨层转移"
    },
    {
      "anchor": "V82-P4227",
      "ordinal": 4227,
      "style": "TableText",
      "text": "3. 承接继承"
    },
    {
      "anchor": "V82-P4228",
      "ordinal": 4228,
      "style": "TableText",
      "text": "4. 保护与退出"
    },
    {
      "anchor": "V82-P4229",
      "ordinal": 4229,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P4230",
      "ordinal": 4230,
      "style": "TableText",
      "text": "1. 承接者、制度载体和有效对象可随相位改变"
    },
    {
      "anchor": "V82-P4231",
      "ordinal": 4231,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P4232",
      "ordinal": 4232,
      "style": "TableText",
      "text": "1. 无方向、生成、承接或制度化过程的系统"
    },
    {
      "anchor": "V82-P4233",
      "ordinal": 4233,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P4234",
      "ordinal": 4234,
      "style": "TableText",
      "text": "1. 个案相位直接代表总体"
    },
    {
      "anchor": "V82-P4235",
      "ordinal": 4235,
      "style": "TableText",
      "text": "2. 人类阶段迁入通用核心"
    },
    {
      "anchor": "V82-P4236",
      "ordinal": 4236,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P4237",
      "ordinal": 4237,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4238",
      "ordinal": 4238,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4239",
      "ordinal": 4239,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P4240",
      "ordinal": 4240,
      "style": "TableText",
      "text": "1. S0"
    },
    {
      "anchor": "V82-P4241",
      "ordinal": 4241,
      "style": "TableText",
      "text": "2. S1"
    },
    {
      "anchor": "V82-P4242",
      "ordinal": 4242,
      "style": "TableText",
      "text": "3. S2"
    },
    {
      "anchor": "V82-P4243",
      "ordinal": 4243,
      "style": "TableText",
      "text": "4. S3"
    },
    {
      "anchor": "V82-P4244",
      "ordinal": 4244,
      "style": "TableText",
      "text": "5. S4"
    },
    {
      "anchor": "V82-P4245",
      "ordinal": 4245,
      "style": "TableText",
      "text": "6. S5"
    },
    {
      "anchor": "V82-P4246",
      "ordinal": 4246,
      "style": "TableText",
      "text": "7. S6"
    },
    {
      "anchor": "V82-P4247",
      "ordinal": 4247,
      "style": "TableText",
      "text": "8. X0转换路径"
    },
    {
      "anchor": "V82-P4248",
      "ordinal": 4248,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P4249",
      "ordinal": 4249,
      "style": "TableText",
      "text": "1. 方向、生成、承接、制度化和反馈变量的同期状态"
    },
    {
      "anchor": "V82-P4250",
      "ordinal": 4250,
      "style": "TableText",
      "text": "2. 相位判据跨观察窗的重复匹配记录"
    },
    {
      "anchor": "V82-P4251",
      "ordinal": 4251,
      "style": "TableText",
      "text": "3. 跳阶、并行、混合、回退、分裂、合并与休眠轨迹"
    },
    {
      "anchor": "V82-P4252",
      "ordinal": 4252,
      "style": "TableText",
      "text": "4. X0中的功能转移、责任继承与有序退场记录"
    },
    {
      "anchor": "V82-P4253",
      "ordinal": 4253,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P4254",
      "ordinal": 4254,
      "style": "TableText",
      "text": "1. 相位变量"
    },
    {
      "anchor": "V82-P4255",
      "ordinal": 4255,
      "style": "TableText",
      "text": "2. 转移记录"
    },
    {
      "anchor": "V82-P4256",
      "ordinal": 4256,
      "style": "TableText",
      "text": "3. 留痕"
    },
    {
      "anchor": "V82-P4257",
      "ordinal": 4257,
      "style": "TableText",
      "text": "4. 承接与制度状态"
    },
    {
      "anchor": "V82-P4258",
      "ordinal": 4258,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P4259",
      "ordinal": 4259,
      "style": "TableText",
      "text": "1. 指向锚点"
    },
    {
      "anchor": "V82-P4260",
      "ordinal": 4260,
      "style": "TableText",
      "text": "2. 生成节点"
    },
    {
      "anchor": "V82-P4261",
      "ordinal": 4261,
      "style": "TableText",
      "text": "3. 承接层"
    },
    {
      "anchor": "V82-P4262",
      "ordinal": 4262,
      "style": "TableText",
      "text": "4. 反馈写回"
    },
    {
      "anchor": "V82-P4263",
      "ordinal": 4263,
      "style": "TableText",
      "text": "5. 结构负荷"
    },
    {
      "anchor": "V82-P4264",
      "ordinal": 4264,
      "style": "TableText",
      "text": "6. 模式相位不要求G3；因果转移另需CAUSAL；迟滞、路径依赖或历史效应另需预注册G3-instance，H5只登记候选留痕"
    },
    {
      "anchor": "V82-P4265",
      "ordinal": 4265,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P4266",
      "ordinal": 4266,
      "style": "TableText",
      "text": "1. 相位判断2. 承接继承3. 退场和修复需求"
    },
    {
      "anchor": "V82-P4267",
      "ordinal": 4267,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P4268",
      "ordinal": 4268,
      "style": "TableText",
      "text": "登记相位观察窗、转移时滞、回退与休眠"
    },
    {
      "anchor": "V82-P4269",
      "ordinal": 4269,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P4270",
      "ordinal": 4270,
      "style": "TableText",
      "text": "记录混合相位、分裂、合并与尺度差异"
    },
    {
      "anchor": "V82-P4271",
      "ordinal": 4271,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P4272",
      "ordinal": 4272,
      "style": "TableText",
      "text": "总体相位无法代表的局部群体和角色"
    },
    {
      "anchor": "V82-P4273",
      "ordinal": 4273,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P4274",
      "ordinal": 4274,
      "style": "TableText",
      "text": "1. 成员"
    },
    {
      "anchor": "V82-P4275",
      "ordinal": 4275,
      "style": "TableText",
      "text": "2. 承接者"
    },
    {
      "anchor": "V82-P4276",
      "ordinal": 4276,
      "style": "TableText",
      "text": "3. 异议者"
    },
    {
      "anchor": "V82-P4277",
      "ordinal": 4277,
      "style": "TableText",
      "text": "4. 退出者"
    },
    {
      "anchor": "V82-P4278",
      "ordinal": 4278,
      "style": "TableText",
      "text": "5. 继承者"
    },
    {
      "anchor": "V82-P4279",
      "ordinal": 4279,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P4280",
      "ordinal": 4280,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4281",
      "ordinal": 4281,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4282",
      "ordinal": 4282,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P4283",
      "ordinal": 4283,
      "style": "TableText",
      "text": "1. 集体行动"
    },
    {
      "anchor": "V82-P4284",
      "ordinal": 4284,
      "style": "TableText",
      "text": "2. 组织结构"
    },
    {
      "anchor": "V82-P4285",
      "ordinal": 4285,
      "style": "TableText",
      "text": "3. 制度记录"
    },
    {
      "anchor": "V82-P4286",
      "ordinal": 4286,
      "style": "TableText",
      "text": "4. 共同记忆"
    },
    {
      "anchor": "V82-P4287",
      "ordinal": 4287,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P4288",
      "ordinal": 4288,
      "style": "TableText",
      "text": "1. 作出相位判断的分析者"
    },
    {
      "anchor": "V82-P4289",
      "ordinal": 4289,
      "style": "TableText",
      "text": "2. 据此行动的决策与授权者"
    },
    {
      "anchor": "V82-P4290",
      "ordinal": 4290,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P4291",
      "ordinal": 4291,
      "style": "TableText",
      "text": "相位不构成健康、成功或正当性等级"
    },
    {
      "anchor": "V82-P4292",
      "ordinal": 4292,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P4293",
      "ordinal": 4293,
      "style": "TableText",
      "text": "适用条件和相位证据充分时至原型匹配级"
    },
    {
      "anchor": "V82-P4294",
      "ordinal": 4294,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P4295",
      "ordinal": 4295,
      "style": "TableText",
      "text": "本变量只生成相位原型匹配、混合状态、不确定性与观察需求描述，不授权试探、推进、合并、退场或淘汰；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P4296",
      "ordinal": 4296,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P4297",
      "ordinal": 4297,
      "style": "TableText",
      "text": "1. 同一集体同时呈现S2承接成形与S5漏洞积累的混合相位"
    },
    {
      "anchor": "V82-P4298",
      "ordinal": 4298,
      "style": "TableText",
      "text": "2. 有序退场X0保持功能转移而不是阶段失败"
    },
    {
      "anchor": "V82-P4299",
      "ordinal": 4299,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P4300",
      "ordinal": 4300,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，成员可经安全可达、反报复通道挑战相位证据、线性假设和道德化使用，并触发与原相位判断或决策链独立的复核"
    },
    {
      "anchor": "V82-P4301",
      "ordinal": 4301,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P4302",
      "ordinal": 4302,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销相位命名及其下游决策效力、实际恢复变量级描述与未决状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P4303",
      "ordinal": 4303,
      "style": "SecH2",
      "text": "A.11　HV11 开放性承担行动（完整接口卡）"
    },
    {
      "anchor": "V82-P4304",
      "ordinal": 4304,
      "style": "CardLabel",
      "text": "A. 身份、命题与适用范围"
    },
    {
      "anchor": "V82-P4305",
      "ordinal": 4305,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4306",
      "ordinal": 4306,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4307",
      "ordinal": 4307,
      "style": "TableText",
      "text": "接口 ID（id）"
    },
    {
      "anchor": "V82-P4308",
      "ordinal": 4308,
      "style": "TableText",
      "text": "HV11"
    },
    {
      "anchor": "V82-P4309",
      "ordinal": 4309,
      "style": "TableText",
      "text": "限定 ID（qualified_id）"
    },
    {
      "anchor": "V82-P4310",
      "ordinal": 4310,
      "style": "TableText",
      "text": "human_variable:HV11"
    },
    {
      "anchor": "V82-P4311",
      "ordinal": 4311,
      "style": "TableText",
      "text": "名称（name）"
    },
    {
      "anchor": "V82-P4312",
      "ordinal": 4312,
      "style": "TableText",
      "text": "开放性承担行动"
    },
    {
      "anchor": "V82-P4313",
      "ordinal": 4313,
      "style": "TableText",
      "text": "主张类型（claim_type）"
    },
    {
      "anchor": "V82-P4314",
      "ordinal": 4314,
      "style": "TableText",
      "text": "H"
    },
    {
      "anchor": "V82-P4315",
      "ordinal": 4315,
      "style": "TableText",
      "text": "合同角色（contract_role）"
    },
    {
      "anchor": "V82-P4316",
      "ordinal": 4316,
      "style": "TableText",
      "text": "human_variable_interface"
    },
    {
      "anchor": "V82-P4317",
      "ordinal": 4317,
      "style": "TableText",
      "text": "命题（proposition）"
    },
    {
      "anchor": "V82-P4318",
      "ordinal": 4318,
      "style": "TableText",
      "text": "开放性承担只观察真实成本、自愿性、方向、替代解释和结构后果，不诊断某人有没有爱。"
    },
    {
      "anchor": "V82-P4319",
      "ordinal": 4319,
      "style": "TableText",
      "text": "适用范围（scope）"
    },
    {
      "anchor": "V82-P4320",
      "ordinal": 4320,
      "style": "TableText",
      "text": "人类关系、组织、制度与公共行动中的承担"
    },
    {
      "anchor": "V82-P4321",
      "ordinal": 4321,
      "style": "TableText",
      "text": "暂停条件（pause_condition）"
    },
    {
      "anchor": "V82-P4322",
      "ordinal": 4322,
      "style": "TableText",
      "text": "无法安全确认自愿、拒绝和退出，或分析转向人格与爱的诊断"
    },
    {
      "anchor": "V82-P4323",
      "ordinal": 4323,
      "style": "CardLabel",
      "text": "B. 正式依赖与推论边界"
    },
    {
      "anchor": "V82-P4324",
      "ordinal": 4324,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4325",
      "ordinal": 4325,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4326",
      "ordinal": 4326,
      "style": "TableText",
      "text": "推论依赖（inferential_requires）"
    },
    {
      "anchor": "V82-P4327",
      "ordinal": 4327,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4328",
      "ordinal": 4328,
      "style": "TableText",
      "text": "协议依赖（protocol_requires）"
    },
    {
      "anchor": "V82-P4329",
      "ordinal": 4329,
      "style": "TableText",
      "text": "1. N4"
    },
    {
      "anchor": "V82-P4330",
      "ordinal": 4330,
      "style": "TableText",
      "text": "2. EVIDENCE"
    },
    {
      "anchor": "V82-P4331",
      "ordinal": 4331,
      "style": "TableText",
      "text": "3. SOURCE"
    },
    {
      "anchor": "V82-P4332",
      "ordinal": 4332,
      "style": "TableText",
      "text": "限定／特化（specializes）"
    },
    {
      "anchor": "V82-P4333",
      "ordinal": 4333,
      "style": "TableText",
      "text": "1. H62. H2"
    },
    {
      "anchor": "V82-P4334",
      "ordinal": 4334,
      "style": "TableText",
      "text": "适用对象引用（applies_to）"
    },
    {
      "anchor": "V82-P4335",
      "ordinal": 4335,
      "style": "TableText",
      "text": "无（空集合）"
    },
    {
      "anchor": "V82-P4336",
      "ordinal": 4336,
      "style": "TableText",
      "text": "条件支持路由（conditional_support_routes）"
    },
    {
      "anchor": "V82-P4337",
      "ordinal": 4337,
      "style": "TableText",
      "text": "1. route_id=HV11-R0-action-cost-record；"
    },
    {
      "anchor": "V82-P4338",
      "ordinal": 4338,
      "style": "TableText",
      "text": "claim_level=normative_boundary；"
    },
    {
      "anchor": "V82-P4339",
      "ordinal": 4339,
      "style": "TableText",
      "text": "when=行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；"
    },
    {
      "anchor": "V82-P4340",
      "ordinal": 4340,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4341",
      "ordinal": 4341,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4342",
      "ordinal": 4342,
      "style": "TableText",
      "text": "allowed_conclusion=描述候选承担行动、成本分布、强制风险、停止权缺口与保护需求。；"
    },
    {
      "anchor": "V82-P4343",
      "ordinal": 4343,
      "style": "TableText",
      "text": "result_ceiling=不得称开放性承担，不得诊断爱、人格或要求继续承担。"
    },
    {
      "anchor": "V82-P4344",
      "ordinal": 4344,
      "style": "TableText",
      "text": "2. route_id=HV11-R1-voluntary-limited-action；"
    },
    {
      "anchor": "V82-P4345",
      "ordinal": 4345,
      "style": "TableText",
      "text": "claim_level=normative_boundary；"
    },
    {
      "anchor": "V82-P4346",
      "ordinal": 4346,
      "style": "TableText",
      "text": "when=真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；"
    },
    {
      "anchor": "V82-P4347",
      "ordinal": 4347,
      "style": "TableText",
      "text": "additional_inferential_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4348",
      "ordinal": 4348,
      "style": "TableText",
      "text": "additional_protocol_requires=无（空集合）；"
    },
    {
      "anchor": "V82-P4349",
      "ordinal": 4349,
      "style": "TableText",
      "text": "allowed_conclusion=登记有限、自愿且具有方向和可观察后果的开放性承担行动描述。；"
    },
    {
      "anchor": "V82-P4350",
      "ordinal": 4350,
      "style": "TableText",
      "text": "result_ceiling=只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。"
    },
    {
      "anchor": "V82-P4351",
      "ordinal": 4351,
      "style": "TableText",
      "text": "3. route_id=HV11-R2-structural-consequence；"
    },
    {
      "anchor": "V82-P4352",
      "ordinal": 4352,
      "style": "TableText",
      "text": "claim_level=conditional_effect；"
    },
    {
      "anchor": "V82-P4353",
      "ordinal": 4353,
      "style": "TableText",
      "text": "when=符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；"
    },
    {
      "anchor": "V82-P4354",
      "ordinal": 4354,
      "style": "TableText",
      "text": "additional_inferential_requires=G2-instance；"
    },
    {
      "anchor": "V82-P4355",
      "ordinal": 4355,
      "style": "TableText",
      "text": "additional_protocol_requires=CAUSAL、E4；"
    },
    {
      "anchor": "V82-P4356",
      "ordinal": 4356,
      "style": "TableText",
      "text": "allowed_conclusion=登记指定通道、对象与窗口内的行动结构后果。；"
    },
    {
      "anchor": "V82-P4357",
      "ordinal": 4357,
      "style": "TableText",
      "text": "result_ceiling=结构效应不证明爱、善、正当性、无限责任或行动授权。"
    },
    {
      "anchor": "V82-P4358",
      "ordinal": 4358,
      "style": "TableText",
      "text": "允许推论（allowed_inference）"
    },
    {
      "anchor": "V82-P4359",
      "ordinal": 4359,
      "style": "TableText",
      "text": "1. 描述有限承担行动与后果"
    },
    {
      "anchor": "V82-P4360",
      "ordinal": 4360,
      "style": "TableText",
      "text": "禁止跳跃（prohibited_leap）"
    },
    {
      "anchor": "V82-P4361",
      "ordinal": 4361,
      "style": "TableText",
      "text": "1. 诊断有没有爱"
    },
    {
      "anchor": "V82-P4362",
      "ordinal": 4362,
      "style": "TableText",
      "text": "2. 牺牲等于爱"
    },
    {
      "anchor": "V82-P4363",
      "ordinal": 4363,
      "style": "TableText",
      "text": "3. 责任等于无限承担"
    },
    {
      "anchor": "V82-P4364",
      "ordinal": 4364,
      "style": "TableText",
      "text": "4. 拒绝等于道德失败"
    },
    {
      "anchor": "V82-P4365",
      "ordinal": 4365,
      "style": "CardLabel",
      "text": "C. 九轴尺度与对象合同"
    },
    {
      "anchor": "V82-P4366",
      "ordinal": 4366,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4367",
      "ordinal": 4367,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4368",
      "ordinal": 4368,
      "style": "TableText",
      "text": "九轴尺度画像（scale_profile）"
    },
    {
      "anchor": "V82-P4369",
      "ordinal": 4369,
      "style": "TableText",
      "text": "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次承担行动、行动者个案、关系或组织总体、成本自愿性分布及聚合规则；X=空间范围：关系与照护现场、组织边界、数字公共空间与跨域受益范围；T=时间跨度：即时行动、持续承担、耗竭、恢复与代际窗口；O=组织层级：行动角色、关系或团队、组织、制度至治理生态；C=因果层次：承担事件、行动—成本互动机制、中观关系结构、制度责任安排与系统条件；R=观察分辨率：原始行动与成本、承担序列、行动者个案、成本自愿性分布、后果指标与摘要，并登记压缩损失；I=影响范围：直接行动者与受益者、依赖者、间接替代承接者、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖照护、受益连接、替代承接、退出路径与跨域成本网络；J=管辖与授权范围：承担要求、资源使用、拒绝、停止、保护与补救分别登记授权；保留自愿成本退出差异"
    },
    {
      "anchor": "V82-P4370",
      "ordinal": 4370,
      "style": "TableText",
      "text": "有效对象（effective_object）"
    },
    {
      "anchor": "V82-P4371",
      "ordinal": 4371,
      "style": "TableText",
      "text": "满足真实成本、自愿性、方向和结构后果条件的人类行动"
    },
    {
      "anchor": "V82-P4372",
      "ordinal": 4372,
      "style": "TableText",
      "text": "跨尺度保持项（scale_invariants）"
    },
    {
      "anchor": "V82-P4373",
      "ordinal": 4373,
      "style": "TableText",
      "text": "1. 成本、自愿性、方向、替代解释、后果与停止权"
    },
    {
      "anchor": "V82-P4374",
      "ordinal": 4374,
      "style": "TableText",
      "text": "升格必补项（required_scale_additions）"
    },
    {
      "anchor": "V82-P4375",
      "ordinal": 4375,
      "style": "TableText",
      "text": "1. 自愿性分布"
    },
    {
      "anchor": "V82-P4376",
      "ordinal": 4376,
      "style": "TableText",
      "text": "2. 代表关系"
    },
    {
      "anchor": "V82-P4377",
      "ordinal": 4377,
      "style": "TableText",
      "text": "3. 成本外溢"
    },
    {
      "anchor": "V82-P4378",
      "ordinal": 4378,
      "style": "TableText",
      "text": "4. 真实退出与代理保护"
    },
    {
      "anchor": "V82-P4379",
      "ordinal": 4379,
      "style": "TableText",
      "text": "随尺度改变项（changing_semantics）"
    },
    {
      "anchor": "V82-P4380",
      "ordinal": 4380,
      "style": "TableText",
      "text": "1. 承担形式、成本位置和受益对象可改变"
    },
    {
      "anchor": "V82-P4381",
      "ordinal": 4381,
      "style": "TableText",
      "text": "不适用对象（non_applicable_objects）"
    },
    {
      "anchor": "V82-P4382",
      "ordinal": 4382,
      "style": "TableText",
      "text": "1. 无意向、自愿性、责任或意义能力的非人系统"
    },
    {
      "anchor": "V82-P4383",
      "ordinal": 4383,
      "style": "TableText",
      "text": "禁止升格（forbidden_elevation）"
    },
    {
      "anchor": "V82-P4384",
      "ordinal": 4384,
      "style": "TableText",
      "text": "1. 个体承担升格为群体义务"
    },
    {
      "anchor": "V82-P4385",
      "ordinal": 4385,
      "style": "TableText",
      "text": "2. 人类承担概念迁入非人核心"
    },
    {
      "anchor": "V82-P4386",
      "ordinal": 4386,
      "style": "CardLabel",
      "text": "D. 状态、证据与变量流"
    },
    {
      "anchor": "V82-P4387",
      "ordinal": 4387,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4388",
      "ordinal": 4388,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4389",
      "ordinal": 4389,
      "style": "TableText",
      "text": "状态集合（state）"
    },
    {
      "anchor": "V82-P4390",
      "ordinal": 4390,
      "style": "TableText",
      "text": "1. 候选"
    },
    {
      "anchor": "V82-P4391",
      "ordinal": 4391,
      "style": "TableText",
      "text": "2. 自愿且有限"
    },
    {
      "anchor": "V82-P4392",
      "ordinal": 4392,
      "style": "TableText",
      "text": "3. 强制风险"
    },
    {
      "anchor": "V82-P4393",
      "ordinal": 4393,
      "style": "TableText",
      "text": "4. 单方耗竭"
    },
    {
      "anchor": "V82-P4394",
      "ordinal": 4394,
      "style": "TableText",
      "text": "5. 停止或退出"
    },
    {
      "anchor": "V82-P4395",
      "ordinal": 4395,
      "style": "TableText",
      "text": "可观测项（observables）"
    },
    {
      "anchor": "V82-P4396",
      "ordinal": 4396,
      "style": "TableText",
      "text": "1. 行动投入的时间、资源、机会与身体心理成本"
    },
    {
      "anchor": "V82-P4397",
      "ordinal": 4397,
      "style": "TableText",
      "text": "2. 拒绝、退出、停止和重新协商是否真实可用"
    },
    {
      "anchor": "V82-P4398",
      "ordinal": 4398,
      "style": "TableText",
      "text": "3. 行动方向、受益位置和可检测结构后果"
    },
    {
      "anchor": "V82-P4399",
      "ordinal": 4399,
      "style": "TableText",
      "text": "4. 强制、恐惧、依赖、利益与表演等替代解释"
    },
    {
      "anchor": "V82-P4400",
      "ordinal": 4400,
      "style": "TableText",
      "text": "证据要求（evidence）"
    },
    {
      "anchor": "V82-P4401",
      "ordinal": 4401,
      "style": "TableText",
      "text": "1. 行动与成本"
    },
    {
      "anchor": "V82-P4402",
      "ordinal": 4402,
      "style": "TableText",
      "text": "2. 拒绝和退出条件"
    },
    {
      "anchor": "V82-P4403",
      "ordinal": 4403,
      "style": "TableText",
      "text": "3. 替代解释"
    },
    {
      "anchor": "V82-P4404",
      "ordinal": 4404,
      "style": "TableText",
      "text": "4. 受益与后果"
    },
    {
      "anchor": "V82-P4405",
      "ordinal": 4405,
      "style": "TableText",
      "text": "输入依赖与接口内容（input_dependencies）"
    },
    {
      "anchor": "V82-P4406",
      "ordinal": 4406,
      "style": "TableText",
      "text": "1. 指向锚点"
    },
    {
      "anchor": "V82-P4407",
      "ordinal": 4407,
      "style": "TableText",
      "text": "2. 承接层"
    },
    {
      "anchor": "V82-P4408",
      "ordinal": 4408,
      "style": "TableText",
      "text": "3. 条件势场"
    },
    {
      "anchor": "V82-P4409",
      "ordinal": 4409,
      "style": "TableText",
      "text": "4. 权力与安全"
    },
    {
      "anchor": "V82-P4410",
      "ordinal": 4410,
      "style": "TableText",
      "text": "输出效应与变量流（output_effects）"
    },
    {
      "anchor": "V82-P4411",
      "ordinal": 4411,
      "style": "TableText",
      "text": "1. 成本分布"
    },
    {
      "anchor": "V82-P4412",
      "ordinal": 4412,
      "style": "TableText",
      "text": "2. 关系和制度状态"
    },
    {
      "anchor": "V82-P4413",
      "ordinal": 4413,
      "style": "TableText",
      "text": "3. 停止与修复"
    },
    {
      "anchor": "V82-P4414",
      "ordinal": 4414,
      "style": "TableText",
      "text": "时间窗与时滞（time_window_and_lag）"
    },
    {
      "anchor": "V82-P4415",
      "ordinal": 4415,
      "style": "TableText",
      "text": "登记即时成本、持续承担、耗竭与恢复时滞"
    },
    {
      "anchor": "V82-P4416",
      "ordinal": 4416,
      "style": "TableText",
      "text": "不确定性（uncertainty）"
    },
    {
      "anchor": "V82-P4417",
      "ordinal": 4417,
      "style": "TableText",
      "text": "记录依赖、恐惧、隐性强制与表达安全"
    },
    {
      "anchor": "V82-P4418",
      "ordinal": 4418,
      "style": "TableText",
      "text": "局部排除区（local_exclusion_zone）"
    },
    {
      "anchor": "V82-P4419",
      "ordinal": 4419,
      "style": "TableText",
      "text": "无法安全拒绝、无法退出或被道德压力遮蔽的位置"
    },
    {
      "anchor": "V82-P4420",
      "ordinal": 4420,
      "style": "TableText",
      "text": "受影响位置（affected_positions）"
    },
    {
      "anchor": "V82-P4421",
      "ordinal": 4421,
      "style": "TableText",
      "text": "1. 行动者"
    },
    {
      "anchor": "V82-P4422",
      "ordinal": 4422,
      "style": "TableText",
      "text": "2. 受益者"
    },
    {
      "anchor": "V82-P4423",
      "ordinal": 4423,
      "style": "TableText",
      "text": "3. 依赖者"
    },
    {
      "anchor": "V82-P4424",
      "ordinal": 4424,
      "style": "TableText",
      "text": "4. 替代承接者"
    },
    {
      "anchor": "V82-P4425",
      "ordinal": 4425,
      "style": "CardLabel",
      "text": "E. 承接、责任、规范、上限与纠错"
    },
    {
      "anchor": "V82-P4426",
      "ordinal": 4426,
      "style": "TableHead",
      "text": "字段"
    },
    {
      "anchor": "V82-P4427",
      "ordinal": 4427,
      "style": "TableHead",
      "text": "登记内容"
    },
    {
      "anchor": "V82-P4428",
      "ordinal": 4428,
      "style": "TableText",
      "text": "承接载体（carrier）"
    },
    {
      "anchor": "V82-P4429",
      "ordinal": 4429,
      "style": "TableText",
      "text": "1. 具体行动者"
    },
    {
      "anchor": "V82-P4430",
      "ordinal": 4430,
      "style": "TableText",
      "text": "2. 关系实践"
    },
    {
      "anchor": "V82-P4431",
      "ordinal": 4431,
      "style": "TableText",
      "text": "3. 照护或责任安排"
    },
    {
      "anchor": "V82-P4432",
      "ordinal": 4432,
      "style": "TableText",
      "text": "责任主体（responsible_subject）"
    },
    {
      "anchor": "V82-P4433",
      "ordinal": 4433,
      "style": "TableText",
      "text": "1. 提出要求者"
    },
    {
      "anchor": "V82-P4434",
      "ordinal": 4434,
      "style": "TableText",
      "text": "2. 授权者"
    },
    {
      "anchor": "V82-P4435",
      "ordinal": 4435,
      "style": "TableText",
      "text": "3. 受益责任者"
    },
    {
      "anchor": "V82-P4436",
      "ordinal": 4436,
      "style": "TableText",
      "text": "4. 补救责任者"
    },
    {
      "anchor": "V82-P4437",
      "ordinal": 4437,
      "style": "TableText",
      "text": "规范地位（normative_status）"
    },
    {
      "anchor": "V82-P4438",
      "ordinal": 4438,
      "style": "TableText",
      "text": "受N4约束，不可命令或征用"
    },
    {
      "anchor": "V82-P4439",
      "ordinal": 4439,
      "style": "TableText",
      "text": "判断上限（judgment_ceiling）"
    },
    {
      "anchor": "V82-P4440",
      "ordinal": 4440,
      "style": "TableText",
      "text": "证据充分时只到行动描述级，不进入人格诊断"
    },
    {
      "anchor": "V82-P4441",
      "ordinal": 4441,
      "style": "TableText",
      "text": "行动上限（action_ceiling）"
    },
    {
      "anchor": "V82-P4442",
      "ordinal": 4442,
      "style": "TableText",
      "text": "本变量只生成自愿性、真实成本、方向、替代解释、结构后果与停止保护需求描述，不授权保护措施、承担要求、资源征用或人格裁决；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
    },
    {
      "anchor": "V82-P4443",
      "ordinal": 4443,
      "style": "TableText",
      "text": "反例（counterexamples）"
    },
    {
      "anchor": "V82-P4444",
      "ordinal": 4444,
      "style": "TableText",
      "text": "1. 无法拒绝的单方牺牲被赞美为爱或责任"
    },
    {
      "anchor": "V82-P4445",
      "ordinal": 4445,
      "style": "TableText",
      "text": "2. 承担宣称没有真实成本、行动方向或可检测结构后果"
    },
    {
      "anchor": "V82-P4446",
      "ordinal": 4446,
      "style": "TableText",
      "text": "申诉（appeal）"
    },
    {
      "anchor": "V82-P4447",
      "ordinal": 4447,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，行动者可经安全可达、反报复通道拒绝被代表，说明强制、成本、替代解释和退出限制，并触发与原承担判断或要求链独立的复核"
    },
    {
      "anchor": "V82-P4448",
      "ordinal": 4448,
      "style": "TableText",
      "text": "回滚（rollback）"
    },
    {
      "anchor": "V82-P4449",
      "ordinal": 4449,
      "style": "TableText",
      "text": "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销承担命名与相关要求，实际恢复拒绝、退出、记录和资源状态，保留版本与完成验证"
    },
    {
      "anchor": "V82-P4450",
      "ordinal": 4450,
      "style": "BodyCJK",
      "text": "scale_profile 不是“微观—宏观”的单轴标签，而是 SP=<A,X,T,O,C,R,I,N,J> 的完整九轴记录：A 是聚合层次，必须声明单元、总体、分布和聚合规则；X 是物理空间与数字边界；T 是窗口、时滞和周期；O 是角色、团队、组织、制度与治理生态的组织层级；C 是事件、互动机制、中观结构、制度和系统条件的因果层次；R 是原始事件、序列、个案、分布、指标与摘要的观察分辨率，并记录压缩损失；I 是直接、间接、二阶、跨域与代际的受影响范围；N 是网络拓扑范围；J 是管辖与授权范围。扩大 A、X、O 或 I 不会自动扩大 J；观察更多不能产生更大处置权。"
    },
    {
      "anchor": "V82-P4451",
      "ordinal": 4451,
      "style": "BodyCJK",
      "text": "身份与同一性判据属于对象合同 K，关系与作用通道进入 input_dependencies、carrier 或因果合同，成员与受影响位置进入 affected_positions、local_exclusion_zone 和观察字段；它们都不能冒充尺度轴。尺度轴 N 指网络拓扑；下文“运行时显式 N 前提”指规范选择层 N1-N5，两者不可混用。"
    },
    {
      "anchor": "V82-P4452",
      "ordinal": 4452,
      "style": "BodyCJK",
      "text": "十一项变量共享同一行动边界：变量本身只生成描述、证据缺口与行动需求，不授权现实调整。其输出上限如下。"
    },
    {
      "anchor": "V82-P4453",
      "ordinal": 4453,
      "style": "TableHead",
      "text": "变量"
    },
    {
      "anchor": "V82-P4454",
      "ordinal": 4454,
      "style": "TableHead",
      "text": "本变量可生成的描述或需求"
    },
    {
      "anchor": "V82-P4455",
      "ordinal": 4455,
      "style": "TableText",
      "text": "HV01"
    },
    {
      "anchor": "V82-P4456",
      "ordinal": 4456,
      "style": "TableText",
      "text": "候选结构域、边界争议与补证需求"
    },
    {
      "anchor": "V82-P4457",
      "ordinal": 4457,
      "style": "TableText",
      "text": "HV02"
    },
    {
      "anchor": "V82-P4458",
      "ordinal": 4458,
      "style": "TableText",
      "text": "边界状态、接口障碍、排除风险与测试需求"
    },
    {
      "anchor": "V82-P4459",
      "ordinal": 4459,
      "style": "TableText",
      "text": "HV03"
    },
    {
      "anchor": "V82-P4460",
      "ordinal": 4460,
      "style": "TableText",
      "text": "候选锚点、异质表达、比较结果与补证需求"
    },
    {
      "anchor": "V82-P4461",
      "ordinal": 4461,
      "style": "TableText",
      "text": "HV04"
    },
    {
      "anchor": "V82-P4462",
      "ordinal": 4462,
      "style": "TableText",
      "text": "GC、GS、GE 候选分型、状态转移与补证需求"
    },
    {
      "anchor": "V82-P4463",
      "ordinal": 4463,
      "style": "TableText",
      "text": "HV05"
    },
    {
      "anchor": "V82-P4464",
      "ordinal": 4464,
      "style": "TableText",
      "text": "CV、RS、成本、容量、停止权、承接缺口及减载、补资源或重分配需求"
    },
    {
      "anchor": "V82-P4465",
      "ordinal": 4465,
      "style": "TableText",
      "text": "HV06"
    },
    {
      "anchor": "V82-P4466",
      "ordinal": 4466,
      "style": "TableText",
      "text": "链条连通、时滞、损耗、中断、成本与承接需求"
    },
    {
      "anchor": "V82-P4467",
      "ordinal": 4467,
      "style": "TableText",
      "text": "HV07"
    },
    {
      "anchor": "V82-P4468",
      "ordinal": 4468,
      "style": "TableText",
      "text": "受理、字段变化、执行、持续时间、写回缺口与程序修复需求"
    },
    {
      "anchor": "V82-P4469",
      "ordinal": 4469,
      "style": "TableText",
      "text": "HV08"
    },
    {
      "anchor": "V82-P4470",
      "ordinal": 4470,
      "style": "TableText",
      "text": "候选条件通道、位置异质性、证据遮蔽与风险降低需求"
    },
    {
      "anchor": "V82-P4471",
      "ordinal": 4471,
      "style": "TableText",
      "text": "HV09"
    },
    {
      "anchor": "V82-P4472",
      "ordinal": 4472,
      "style": "TableText",
      "text": "负荷、容量、恢复、局部过载与减载补资源需求"
    },
    {
      "anchor": "V82-P4473",
      "ordinal": 4473,
      "style": "TableText",
      "text": "HV10"
    },
    {
      "anchor": "V82-P4474",
      "ordinal": 4474,
      "style": "TableText",
      "text": "相位原型匹配、混合状态、不确定性与观察需求"
    },
    {
      "anchor": "V82-P4475",
      "ordinal": 4475,
      "style": "TableText",
      "text": "HV11"
    },
    {
      "anchor": "V82-P4476",
      "ordinal": 4476,
      "style": "TableText",
      "text": "自愿性、真实成本、方向、替代解释、结构后果与停止保护需求"
    },
    {
      "anchor": "V82-P4477",
      "ordinal": 4477,
      "style": "BodyCJK",
      "text": "无论需求看起来多么明显，任何现实调整都须另过 C12、运行时显式 N 前提、J 授权与 O 程序。变量不得自行授权测试、减载、补资源、修复、保护、归责、试探、推进、退出安排或处置。"
    }
  ],
  "tables": [
    {
      "anchor": "V82-T064",
      "cell_paragraph_ordinals": [
        [
          [
            2911
          ],
          [
            2912
          ]
        ],
        [
          [
            2913
          ],
          [
            2914
          ]
        ],
        [
          [
            2915
          ],
          [
            2916
          ]
        ],
        [
          [
            2917
          ],
          [
            2918
          ]
        ],
        [
          [
            2919
          ],
          [
            2920
          ]
        ],
        [
          [
            2921
          ],
          [
            2922
          ]
        ],
        [
          [
            2923
          ],
          [
            2924
          ]
        ],
        [
          [
            2925
          ],
          [
            2926
          ]
        ],
        [
          [
            2927
          ],
          [
            2928
          ]
        ]
      ],
      "ordinal": 64,
      "paragraph_ordinals": [
        2911,
        2912,
        2913,
        2914,
        2915,
        2916,
        2917,
        2918,
        2919,
        2920,
        2921,
        2922,
        2923,
        2924,
        2925,
        2926,
        2927,
        2928
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV01"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV01"
        ],
        [
          "名称（name）",
          "结构域"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "D0只声明候选人类对象；只有预注册G1-instance显示候选分组相对匹配N0在预选结果上取得超过阈值的样本外或外推增益时，才在该实例范围登记有限有效结构域。"
        ],
        [
          "适用范围（scope）",
          "关系、团队、组织、制度与公共议题"
        ],
        [
          "暂停条件（pause_condition）",
          "对象、边界、尺度、时间窗、同一性或零模型不完整"
        ]
      ]
    },
    {
      "anchor": "V82-T065",
      "cell_paragraph_ordinals": [
        [
          [
            2930
          ],
          [
            2931
          ]
        ],
        [
          [
            2932
          ],
          [
            2933
          ]
        ],
        [
          [
            2934
          ],
          [
            2935,
            2936,
            2937
          ]
        ],
        [
          [
            2938
          ],
          [
            2939
          ]
        ],
        [
          [
            2940
          ],
          [
            2941
          ]
        ],
        [
          [
            2942
          ],
          [
            2943,
            2944,
            2945,
            2946,
            2947,
            2948,
            2949,
            2950,
            2951,
            2952,
            2953,
            2954,
            2955,
            2956
          ]
        ],
        [
          [
            2957
          ],
          [
            2958
          ]
        ],
        [
          [
            2959
          ],
          [
            2960
          ]
        ]
      ],
      "ordinal": 65,
      "paragraph_ordinals": [
        2930,
        2931,
        2932,
        2933,
        2934,
        2935,
        2936,
        2937,
        2938,
        2939,
        2940,
        2941,
        2942,
        2943,
        2944,
        2945,
        2946,
        2947,
        2948,
        2949,
        2950,
        2951,
        2952,
        2953,
        2954,
        2955,
        2956,
        2957,
        2958,
        2959,
        2960
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "1. D0"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. E1\n2. EVIDENCE\n3. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV01-R0-candidate-object；\nclaim_level=candidate_description；\nwhen=D0对象合同完整，但尚无符合资格且result_state=supported的G1-instance。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记候选人类对象、材料集合、边界争议与G1补证需求。；\nresult_ceiling=仅到候选对象描述；不得称有限有效结构域，也不得限定HV02-HV11的经验对象范围。\n2. route_id=HV01-R1-effective-domain；\nclaim_level=descriptive_classification；\nwhen=同一对象、尺度、窗口、K与外推单元内的预注册G1-instance取得supported。；\nadditional_inferential_requires=G1-instance；\nadditional_protocol_requires=E4；\nallowed_conclusion=登记该实例范围内的有限有效结构域、对象识别强度、边界可信度和适用窗。；\nresult_ceiling=只限预注册SP/T/K与generalization_unit；不得作终极本体、统一意志或授权判断。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 只在G1-instance预注册对象、尺度、窗口、结果与外推单位内登记有限有效结构域及识别强度"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 命名即客观共同体2. 共同处境即共同意愿"
        ]
      ]
    },
    {
      "anchor": "V82-T066",
      "cell_paragraph_ordinals": [
        [
          [
            2962
          ],
          [
            2963
          ]
        ],
        [
          [
            2964
          ],
          [
            2965
          ]
        ],
        [
          [
            2966
          ],
          [
            2967
          ]
        ],
        [
          [
            2968
          ],
          [
            2969
          ]
        ],
        [
          [
            2970
          ],
          [
            2971,
            2972,
            2973,
            2974
          ]
        ],
        [
          [
            2975
          ],
          [
            2976
          ]
        ],
        [
          [
            2977
          ],
          [
            2978
          ]
        ],
        [
          [
            2979
          ],
          [
            2980
          ]
        ]
      ],
      "ordinal": 66,
      "paragraph_ordinals": [
        2962,
        2963,
        2964,
        2965,
        2966,
        2967,
        2968,
        2969,
        2970,
        2971,
        2972,
        2973,
        2974,
        2975,
        2976,
        2977,
        2978,
        2979,
        2980
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：关系或事件单元、候选成员总体、边界内外分布及分组规则；X=空间范围：共同场所、组织边界、数字平台与跨域外部环境；T=时间跨度：识别窗口、成员变动周期与边界历史；O=组织层级：角色、团队、组织、制度至治理生态；C=因果层次：原始事件、互动机制、中观关系结构、制度与系统条件；R=观察分辨率：原始互动、事件序列、成员个案、边界分布、指标与摘要，并登记压缩损失；I=影响范围：直接成员、被排除者、间接受影响者、二阶外溢、跨域与代际位置；N=网络拓扑范围：成员关系、边界连接、孤立点与跨域桥接；J=管辖与授权范围：对象命名、边界采用及后续处置分别登记授权；不适用轴须登记not_applicable理由"
        ],
        [
          "有效对象（effective_object）",
          "由D0声明的候选对象；只有通过预注册G1-instance相对匹配N0的阈值检验后，才在该实例范围登记为有限有效结构域"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 对象合同2. 参与与受影响位置"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 单位与总体\n2. 代表性\n3. J轴\n4. 低可见位置"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 有效成员、关系和同一性可随尺度改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无意向、制度或责任接口的非人系统"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 局部群体直接代表全部受影响者"
        ]
      ]
    },
    {
      "anchor": "V82-T067",
      "cell_paragraph_ordinals": [
        [
          [
            2982
          ],
          [
            2983
          ]
        ],
        [
          [
            2984
          ],
          [
            2985
          ]
        ],
        [
          [
            2986
          ],
          [
            2987,
            2988,
            2989,
            2990
          ]
        ],
        [
          [
            2991
          ],
          [
            2992,
            2993,
            2994,
            2995
          ]
        ],
        [
          [
            2996
          ],
          [
            2997,
            2998,
            2999
          ]
        ],
        [
          [
            3000
          ],
          [
            3001
          ]
        ],
        [
          [
            3002
          ],
          [
            3003
          ]
        ],
        [
          [
            3004
          ],
          [
            3005
          ]
        ],
        [
          [
            3006
          ],
          [
            3007
          ]
        ],
        [
          [
            3008
          ],
          [
            3009
          ]
        ]
      ],
      "ordinal": 67,
      "paragraph_ordinals": [
        2982,
        2983,
        2984,
        2985,
        2986,
        2987,
        2988,
        2989,
        2990,
        2991,
        2992,
        2993,
        2994,
        2995,
        2996,
        2997,
        2998,
        2999,
        3000,
        3001,
        3002,
        3003,
        3004,
        3005,
        3006,
        3007,
        3008,
        3009
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 候选2. 可识别3. 边界争议4. 不成立"
        ],
        [
          "可观测项（observables）",
          "1. 边界内外关系密度与约束差异\n2. 成员进入、退出与被排除记录\n3. 共同问题、资源通道或制度规则的重复共现\n4. 改变分组规则后对象识别是否稳定"
        ],
        [
          "证据要求（evidence）",
          "1. D0候选对象与同一性记录\n2. G1-instance预注册表及匹配N0\n3. 训练与样本外或外推结果\n4. 候选分组与竞争分组的增益比较"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. D0只提供候选对象字段，不构成结构成立证据\n2. 预注册G1-instance及匹配N0、阈值、模型类、样本或外推单位\n3. 观察位置、竞争分组与E1协议"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 仅在G1-instance通过后限定其余十变量的对象范围；未通过时保持候选或材料集合"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记识别窗口、边界变动与成员变化时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录边界争议、成员缺席和观察覆盖"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "无法安全表达或未被采样的位置不得被总体代表"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 成员2. 被排除者3. 边界外成本承担者"
        ]
      ]
    },
    {
      "anchor": "V82-T068",
      "cell_paragraph_ordinals": [
        [
          [
            3011
          ],
          [
            3012
          ]
        ],
        [
          [
            3013
          ],
          [
            3014
          ]
        ],
        [
          [
            3015
          ],
          [
            3016,
            3017
          ]
        ],
        [
          [
            3018
          ],
          [
            3019
          ]
        ],
        [
          [
            3020
          ],
          [
            3021
          ]
        ],
        [
          [
            3022
          ],
          [
            3023
          ]
        ],
        [
          [
            3024
          ],
          [
            3025,
            3026
          ]
        ],
        [
          [
            3027
          ],
          [
            3028
          ]
        ],
        [
          [
            3029
          ],
          [
            3030
          ]
        ]
      ],
      "ordinal": 68,
      "paragraph_ordinals": [
        3011,
        3012,
        3013,
        3014,
        3015,
        3016,
        3017,
        3018,
        3019,
        3020,
        3021,
        3022,
        3023,
        3024,
        3025,
        3026,
        3027,
        3028,
        3029,
        3030
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 关系网络2. 组织边界3. 制度记录"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 提出结构域判断的分析者\n2. 使用该判断的决策者"
        ],
        [
          "规范地位（normative_status）",
          "描述性H-World接口，不产生正当性"
        ],
        [
          "判断上限（judgment_ceiling）",
          "只有G1-instance通过时，且仅限预注册对象、尺度、窗口、结果与外推单位，才可登记解释级有限有效对象；否则仅为候选对象或材料集合"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成候选结构域、边界争议与补证需求描述，不授权纳入、排除或处置；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 同一场所中反复共现的人群没有稳定关系或共同约束\n2. 分析者划定的群组在改变分组规则后立即消失"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，成员与受影响位置可经安全可达、反报复通道挑战边界、代表性和同一性判据，并触发与原命名或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销结构域登记、移除其对下游对象范围的效力并恢复为材料集合，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T069",
      "cell_paragraph_ordinals": [
        [
          [
            3033
          ],
          [
            3034
          ]
        ],
        [
          [
            3035
          ],
          [
            3036
          ]
        ],
        [
          [
            3037
          ],
          [
            3038
          ]
        ],
        [
          [
            3039
          ],
          [
            3040
          ]
        ],
        [
          [
            3041
          ],
          [
            3042
          ]
        ],
        [
          [
            3043
          ],
          [
            3044
          ]
        ],
        [
          [
            3045
          ],
          [
            3046
          ]
        ],
        [
          [
            3047
          ],
          [
            3048
          ]
        ],
        [
          [
            3049
          ],
          [
            3050
          ]
        ]
      ],
      "ordinal": 69,
      "paragraph_ordinals": [
        3033,
        3034,
        3035,
        3036,
        3037,
        3038,
        3039,
        3040,
        3041,
        3042,
        3043,
        3044,
        3045,
        3046,
        3047,
        3048,
        3049,
        3050
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV02"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV02"
        ],
        [
          "名称（name）",
          "边界与接口"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "人类边界必须同时登记成员、资源、信息、权利、责任与跨界接口。"
        ],
        [
          "适用范围（scope）",
          "存在纳入、排除、交换或管辖的人类结构"
        ],
        [
          "暂停条件（pause_condition）",
          "正式边界与实际边界混同或排除项不可见"
        ]
      ]
    },
    {
      "anchor": "V82-T070",
      "cell_paragraph_ordinals": [
        [
          [
            3052
          ],
          [
            3053
          ]
        ],
        [
          [
            3054
          ],
          [
            3055
          ]
        ],
        [
          [
            3056
          ],
          [
            3057,
            3058,
            3059
          ]
        ],
        [
          [
            3060
          ],
          [
            3061
          ]
        ],
        [
          [
            3062
          ],
          [
            3063
          ]
        ],
        [
          [
            3064
          ],
          [
            3065,
            3066,
            3067,
            3068,
            3069,
            3070,
            3071,
            3072,
            3073,
            3074,
            3075,
            3076,
            3077,
            3078
          ]
        ],
        [
          [
            3079
          ],
          [
            3080
          ]
        ],
        [
          [
            3081
          ],
          [
            3082,
            3083,
            3084
          ]
        ]
      ],
      "ordinal": 70,
      "paragraph_ordinals": [
        3052,
        3053,
        3054,
        3055,
        3056,
        3057,
        3058,
        3059,
        3060,
        3061,
        3062,
        3063,
        3064,
        3065,
        3066,
        3067,
        3068,
        3069,
        3070,
        3071,
        3072,
        3073,
        3074,
        3075,
        3076,
        3077,
        3078,
        3079,
        3080,
        3081,
        3082,
        3083,
        3084
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "1. human_variable:HV01"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. E1\n2. EVIDENCE\n3. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV02-R0-boundary-inventory；\nclaim_level=descriptive_classification；\nwhen=成员、资源、信息、权利、责任、跨界接口及正式—实际边界差异可逐项登记。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=描述边界状态、接口通达性、守门位置、拒绝记录与排除风险。；\nresult_ceiling=只到边界与接口清单；不得断言边界已产生因果选择效应。\n2. route_id=HV02-R1-selective-effect；\nclaim_level=conditional_effect；\nwhen=预注册边界或接口变动经符合资格的G2-instance显示对指定跨界流、准入或拒绝结果有超过阈值的通道效应。；\nadditional_inferential_requires=G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定通道、窗口与位置上的边界选择效应及跨界成本分布。；\nresult_ceiling=只限已检验通道与结果；不得从空间、组织或影响范围推出J轴管辖与处置权。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 边界选择性2. 接口通达性3. 跨界成本"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 边界等于封闭\n2. 成员身份等于同意\n3. 影响范围等于管辖权"
        ]
      ]
    },
    {
      "anchor": "V82-T071",
      "cell_paragraph_ordinals": [
        [
          [
            3086
          ],
          [
            3087
          ]
        ],
        [
          [
            3088
          ],
          [
            3089
          ]
        ],
        [
          [
            3090
          ],
          [
            3091
          ]
        ],
        [
          [
            3092
          ],
          [
            3093
          ]
        ],
        [
          [
            3094
          ],
          [
            3095,
            3096,
            3097,
            3098
          ]
        ],
        [
          [
            3099
          ],
          [
            3100
          ]
        ],
        [
          [
            3101
          ],
          [
            3102
          ]
        ],
        [
          [
            3103
          ],
          [
            3104
          ]
        ]
      ],
      "ordinal": 71,
      "paragraph_ordinals": [
        3086,
        3087,
        3088,
        3089,
        3090,
        3091,
        3092,
        3093,
        3094,
        3095,
        3096,
        3097,
        3098,
        3099,
        3100,
        3101,
        3102,
        3103,
        3104
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次跨界事件、接口使用个案、成员类别总体、准入拒绝分布及聚合规则；X=空间范围：物理入口、组织边界、数字接口、司法辖区与跨域通道；T=时间跨度：边界生效期、接口等待、迁移时滞与重组周期；O=组织层级：使用者角色、守门团队、组织、制度至治理生态；C=因果层次：跨界事件、守门互动机制、接口结构、制度规则与系统条件；R=观察分辨率：原始准入拒绝记录、使用序列、个案、流量分布、服务指标与摘要，并登记压缩损失；I=影响范围：直接使用者、被排除者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：接口节点、守门瓶颈、替代路径与跨域连接；J=管辖与授权范围：纳入、排除、接口改变及权利责任调整分别登记授权；升格须记录逐轴差值"
        ],
        [
          "有效对象（effective_object）",
          "对资源、信息、权利或责任流产生选择性的边界"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 内外位置2. 跨界通道3. 权利责任边界"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 新成员类别\n2. 跨域接口\n3. 代表与授权\n4. 保护继承"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 成员、接口与实际控制边界可改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无成员、权利或责任概念的非人边界"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 空间或组织范围扩大自动产生管辖权"
        ]
      ]
    },
    {
      "anchor": "V82-T072",
      "cell_paragraph_ordinals": [
        [
          [
            3106
          ],
          [
            3107
          ]
        ],
        [
          [
            3108
          ],
          [
            3109,
            3110,
            3111,
            3112,
            3113
          ]
        ],
        [
          [
            3114
          ],
          [
            3115,
            3116,
            3117,
            3118
          ]
        ],
        [
          [
            3119
          ],
          [
            3120,
            3121,
            3122
          ]
        ],
        [
          [
            3123
          ],
          [
            3124
          ]
        ],
        [
          [
            3125
          ],
          [
            3126,
            3127,
            3128
          ]
        ],
        [
          [
            3129
          ],
          [
            3130
          ]
        ],
        [
          [
            3131
          ],
          [
            3132
          ]
        ],
        [
          [
            3133
          ],
          [
            3134
          ]
        ],
        [
          [
            3135
          ],
          [
            3136,
            3137,
            3138,
            3139
          ]
        ]
      ],
      "ordinal": 72,
      "paragraph_ordinals": [
        3106,
        3107,
        3108,
        3109,
        3110,
        3111,
        3112,
        3113,
        3114,
        3115,
        3116,
        3117,
        3118,
        3119,
        3120,
        3121,
        3122,
        3123,
        3124,
        3125,
        3126,
        3127,
        3128,
        3129,
        3130,
        3131,
        3132,
        3133,
        3134,
        3135,
        3136,
        3137,
        3138,
        3139
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 开放\n2. 选择性开放\n3. 封闭\n4. 争议\n5. 重组"
        ],
        [
          "可观测项（observables）",
          "1. 成员资格、准入与退出决定\n2. 资源、信息、权利和责任的跨界流量\n3. 守门节点、等待时间与拒绝理由\n4. 正式边界与实际通行边界的差异"
        ],
        [
          "证据要求（evidence）",
          "1. 成员名单与例外\n2. 接口使用记录\n3. 跨界流和拒绝记录"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. HV01结构域2. 角色与授权"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. HV05承接\n2. HV07写回\n3. PF-9退出"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "记录边界生效、变更、退出和申诉时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录非正式边界、代理访问和数字空间漂移"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "无法接入接口、无法退出或受保护不公开的位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 成员\n2. 申请者\n3. 被排除者\n4. 边界外承担者"
        ]
      ]
    },
    {
      "anchor": "V82-T073",
      "cell_paragraph_ordinals": [
        [
          [
            3141
          ],
          [
            3142
          ]
        ],
        [
          [
            3143
          ],
          [
            3144,
            3145,
            3146,
            3147
          ]
        ],
        [
          [
            3148
          ],
          [
            3149
          ]
        ],
        [
          [
            3150
          ],
          [
            3151
          ]
        ],
        [
          [
            3152
          ],
          [
            3153
          ]
        ],
        [
          [
            3154
          ],
          [
            3155
          ]
        ],
        [
          [
            3156
          ],
          [
            3157,
            3158
          ]
        ],
        [
          [
            3159
          ],
          [
            3160
          ]
        ],
        [
          [
            3161
          ],
          [
            3162
          ]
        ]
      ],
      "ordinal": 73,
      "paragraph_ordinals": [
        3141,
        3142,
        3143,
        3144,
        3145,
        3146,
        3147,
        3148,
        3149,
        3150,
        3151,
        3152,
        3153,
        3154,
        3155,
        3156,
        3157,
        3158,
        3159,
        3160,
        3161,
        3162
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 成员规则\n2. 访问机制\n3. 法律或制度边界\n4. 技术接口"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 边界制定者2. 接口运营者3. 授权者"
        ],
        [
          "规范地位（normative_status）",
          "边界事实与边界正当性分离"
        ],
        [
          "判断上限（judgment_ceiling）",
          "接口与影响证据充分时至诊断级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成边界状态、接口障碍、排除风险与测试需求描述，不授权改变准入、退出、权利或资源流；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 正式成员边界与实际资源控制边界相反\n2. 数字接口开放但物理、语言或安全门槛使部分位置无法进入"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，边界内外受影响者可经安全可达、反报复通道挑战纳入、排除和接口障碍，并触发与原边界决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正成员与拒绝记录、实际恢复受影响的准入权利或接口状态并撤销错误边界行动，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T074",
      "cell_paragraph_ordinals": [
        [
          [
            3165
          ],
          [
            3166
          ]
        ],
        [
          [
            3167
          ],
          [
            3168
          ]
        ],
        [
          [
            3169
          ],
          [
            3170
          ]
        ],
        [
          [
            3171
          ],
          [
            3172
          ]
        ],
        [
          [
            3173
          ],
          [
            3174
          ]
        ],
        [
          [
            3175
          ],
          [
            3176
          ]
        ],
        [
          [
            3177
          ],
          [
            3178
          ]
        ],
        [
          [
            3179
          ],
          [
            3180
          ]
        ],
        [
          [
            3181
          ],
          [
            3182
          ]
        ]
      ],
      "ordinal": 74,
      "paragraph_ordinals": [
        3165,
        3166,
        3167,
        3168,
        3169,
        3170,
        3171,
        3172,
        3173,
        3174,
        3175,
        3176,
        3177,
        3178,
        3179,
        3180,
        3181,
        3182
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV03"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV03"
        ],
        [
          "名称（name）",
          "指向锚点"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "目标、身份、记忆、承诺、恐惧或共同问题只有改变资源与行动时才构成指向锚点。"
        ],
        [
          "适用范围（scope）",
          "具有意向、协调或共同问题的人类结构"
        ],
        [
          "暂停条件（pause_condition）",
          "只有口号、解释者投射或被强制的一致表达"
        ]
      ]
    },
    {
      "anchor": "V82-T075",
      "cell_paragraph_ordinals": [
        [
          [
            3184
          ],
          [
            3185
          ]
        ],
        [
          [
            3186
          ],
          [
            3187
          ]
        ],
        [
          [
            3188
          ],
          [
            3189,
            3190,
            3191
          ]
        ],
        [
          [
            3192
          ],
          [
            3193
          ]
        ],
        [
          [
            3194
          ],
          [
            3195
          ]
        ],
        [
          [
            3196
          ],
          [
            3197,
            3198,
            3199,
            3200,
            3201,
            3202,
            3203,
            3204,
            3205,
            3206,
            3207,
            3208,
            3209,
            3210
          ]
        ],
        [
          [
            3211
          ],
          [
            3212
          ]
        ],
        [
          [
            3213
          ],
          [
            3214,
            3215,
            3216
          ]
        ]
      ],
      "ordinal": 75,
      "paragraph_ordinals": [
        3184,
        3185,
        3186,
        3187,
        3188,
        3189,
        3190,
        3191,
        3192,
        3193,
        3194,
        3195,
        3196,
        3197,
        3198,
        3199,
        3200,
        3201,
        3202,
        3203,
        3204,
        3205,
        3206,
        3207,
        3208,
        3209,
        3210,
        3211,
        3212,
        3213,
        3214,
        3215,
        3216
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "1. human_variable:HV01"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. E2\n2. EVIDENCE\n3. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV03-R0-candidate-anchor；\nclaim_level=candidate_description；\nwhen=目标、身份、记忆、承诺、恐惧或共同问题有可追踪表达与承载形式，但尚无符合资格的H1-instance。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记候选意义材料、异质表达、代表性争议与H1补证需求。；\nresult_ceiling=仅称候选意义表达；不得称有效指向锚点或共同意志。\n2. route_id=HV03-R1-effective-anchor；\nclaim_level=conditional_effect；\nwhen=预注册H1-instance在资源配置、行动选择或协调结果中唯一预选的判据取得supported。；\nadditional_inferential_requires=H1-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记该实例、结果家族、尺度与窗口内的条件性有效指向锚点。；\nresult_ceiling=不外推到未选资源、行动或协调结果，也不推出真实同意、统一内心或强制统一意义。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 条件性的协调方向与冲突锚点"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 群体具有统一内心\n2. 共同语言等于真实同意\n3. 目标正当"
        ]
      ]
    },
    {
      "anchor": "V82-T076",
      "cell_paragraph_ordinals": [
        [
          [
            3218
          ],
          [
            3219
          ]
        ],
        [
          [
            3220
          ],
          [
            3221
          ]
        ],
        [
          [
            3222
          ],
          [
            3223
          ]
        ],
        [
          [
            3224
          ],
          [
            3225
          ]
        ],
        [
          [
            3226
          ],
          [
            3227,
            3228,
            3229,
            3230
          ]
        ],
        [
          [
            3231
          ],
          [
            3232
          ]
        ],
        [
          [
            3233
          ],
          [
            3234
          ]
        ],
        [
          [
            3235
          ],
          [
            3236
          ]
        ]
      ],
      "ordinal": 76,
      "paragraph_ordinals": [
        3218,
        3219,
        3220,
        3221,
        3222,
        3223,
        3224,
        3225,
        3226,
        3227,
        3228,
        3229,
        3230,
        3231,
        3232,
        3233,
        3234,
        3235,
        3236
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次表达或行动、主体个案、候选参与总体、立场分布及聚合规则；X=空间范围：关系现场、组织空间、数字公共空间与跨域传播范围；T=时间跨度：表达—行动窗口、承诺周期、漂移与解耦时滞；O=组织层级：行动角色、团队、组织、制度至公共治理生态；C=因果层次：表达事件、意义—行动互动机制、中观协调结构、制度安排与系统条件；R=观察分辨率：原始表达与行动、事件序列、个案、立场分布、协调指标与摘要，并登记压缩损失；I=影响范围：直接参与者、异议者、间接受影响者、二阶协调后果、跨域与代际影响；N=网络拓扑范围：表达传播、协调连接、异质簇群与桥接节点；J=管辖与授权范围：锚点命名、代表性采用、协调或统一要求分别登记授权；必须保留异质锚点"
        ],
        [
          "有效对象（effective_object）",
          "能改变资源或行动的目标、身份、记忆、承诺、恐惧或共同问题"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 意义到资源或行动的桥接"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 代表规则\n2. 异质性\n3. 成本收益分布\n4. J轴"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 锚点内容、强度和承载主体可改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无意向、意义或承诺能力的非人系统"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 局部表达直接升级为共同意志"
        ]
      ]
    },
    {
      "anchor": "V82-T077",
      "cell_paragraph_ordinals": [
        [
          [
            3238
          ],
          [
            3239
          ]
        ],
        [
          [
            3240
          ],
          [
            3241,
            3242,
            3243,
            3244,
            3245
          ]
        ],
        [
          [
            3246
          ],
          [
            3247,
            3248,
            3249,
            3250
          ]
        ],
        [
          [
            3251
          ],
          [
            3252,
            3253,
            3254,
            3255
          ]
        ],
        [
          [
            3256
          ],
          [
            3257
          ]
        ],
        [
          [
            3258
          ],
          [
            3259
          ]
        ],
        [
          [
            3260
          ],
          [
            3261
          ]
        ],
        [
          [
            3262
          ],
          [
            3263
          ]
        ],
        [
          [
            3264
          ],
          [
            3265
          ]
        ],
        [
          [
            3266
          ],
          [
            3267,
            3268,
            3269,
            3270
          ]
        ]
      ],
      "ordinal": 77,
      "paragraph_ordinals": [
        3238,
        3239,
        3240,
        3241,
        3242,
        3243,
        3244,
        3245,
        3246,
        3247,
        3248,
        3249,
        3250,
        3251,
        3252,
        3253,
        3254,
        3255,
        3256,
        3257,
        3258,
        3259,
        3260,
        3261,
        3262,
        3263,
        3264,
        3265,
        3266,
        3267,
        3268,
        3269,
        3270
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 分散\n2. 凝聚\n3. 竞争\n4. 固化\n5. 解耦"
        ],
        [
          "可观测项（observables）",
          "1. 预注册意义表达出现前后的资源配置差异\n2. 行动选择、协作完成率或冲突模式变化\n3. 不同位置对锚点的接受、拒绝与替代表述\n4. 比较条件下结果差异是否超过预定阈值"
        ],
        [
          "证据要求（evidence）",
          "1. 资源调整\n2. 行动序列\n3. 承诺与退出记录\n4. 冲突证据"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 参与位置2. 表达安全3. 资源与行动数据"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 生成事件2. 承接动员3. 规范选择议程"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "区分短期口号、长期承诺与代际记忆"
        ],
        [
          "不确定性（uncertainty）",
          "记录沉默、强制一致与内部异质性"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "低安全位置的不同目标不得被聚合抹去"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 认同者\n2. 异议者\n3. 被代表者\n4. 成本承担者"
        ]
      ]
    },
    {
      "anchor": "V82-T078",
      "cell_paragraph_ordinals": [
        [
          [
            3272
          ],
          [
            3273
          ]
        ],
        [
          [
            3274
          ],
          [
            3275,
            3276,
            3277,
            3278,
            3279
          ]
        ],
        [
          [
            3280
          ],
          [
            3281
          ]
        ],
        [
          [
            3282
          ],
          [
            3283
          ]
        ],
        [
          [
            3284
          ],
          [
            3285
          ]
        ],
        [
          [
            3286
          ],
          [
            3287
          ]
        ],
        [
          [
            3288
          ],
          [
            3289,
            3290
          ]
        ],
        [
          [
            3291
          ],
          [
            3292
          ]
        ],
        [
          [
            3293
          ],
          [
            3294
          ]
        ]
      ],
      "ordinal": 78,
      "paragraph_ordinals": [
        3272,
        3273,
        3274,
        3275,
        3276,
        3277,
        3278,
        3279,
        3280,
        3281,
        3282,
        3283,
        3284,
        3285,
        3286,
        3287,
        3288,
        3289,
        3290,
        3291,
        3292,
        3293,
        3294
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 叙事\n2. 承诺\n3. 共同记忆\n4. 制度目标\n5. 问题定义"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 提出代表性主张者2. 据此配置资源者"
        ],
        [
          "规范地位（normative_status）",
          "锚点存在不证明其正当"
        ],
        [
          "判断上限（judgment_ceiling）",
          "有行动桥接时至解释级，无桥接时仅描述表达"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成候选锚点、异质表达、比较结果与补证需求描述，不授权统一意义、代表意愿或协调行动；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 反复出现的口号没有改变任何资源配置或行动\n2. 高压场景中的一致表达掩盖相互冲突的真实目标"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，成员可经安全可达、反报复通道否认代表性、提交异质目标或拒绝被锚定，并触发与原锚点判断链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销锚点命名、移除其代表性与下游协调效力并恢复异质表达状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T079",
      "cell_paragraph_ordinals": [
        [
          [
            3297
          ],
          [
            3298
          ]
        ],
        [
          [
            3299
          ],
          [
            3300
          ]
        ],
        [
          [
            3301
          ],
          [
            3302
          ]
        ],
        [
          [
            3303
          ],
          [
            3304
          ]
        ],
        [
          [
            3305
          ],
          [
            3306
          ]
        ],
        [
          [
            3307
          ],
          [
            3308
          ]
        ],
        [
          [
            3309
          ],
          [
            3310
          ]
        ],
        [
          [
            3311
          ],
          [
            3312
          ]
        ],
        [
          [
            3313
          ],
          [
            3314
          ]
        ]
      ],
      "ordinal": 79,
      "paragraph_ordinals": [
        3297,
        3298,
        3299,
        3300,
        3301,
        3302,
        3303,
        3304,
        3305,
        3306,
        3307,
        3308,
        3309,
        3310,
        3311,
        3312,
        3313,
        3314
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV04"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV04"
        ],
        [
          "名称（name）",
          "生成节点"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "生成必须分流为生成条件GC、生成主体GS与生成事件GE，允许无可识别主体的涌现型生成。"
        ],
        [
          "适用范围（scope）",
          "人类结构中新行动、组织、制度或状态转移的形成"
        ],
        [
          "暂停条件（pause_condition）",
          "条件被人格化、事件被当作主体或主体资格不明"
        ]
      ]
    },
    {
      "anchor": "V82-T080",
      "cell_paragraph_ordinals": [
        [
          [
            3316
          ],
          [
            3317
          ]
        ],
        [
          [
            3318
          ],
          [
            3319
          ]
        ],
        [
          [
            3320
          ],
          [
            3321
          ]
        ],
        [
          [
            3322
          ],
          [
            3323
          ]
        ],
        [
          [
            3324
          ],
          [
            3325
          ]
        ],
        [
          [
            3326
          ],
          [
            3327,
            3328,
            3329,
            3330,
            3331,
            3332,
            3333,
            3334,
            3335,
            3336,
            3337,
            3338,
            3339,
            3340
          ]
        ],
        [
          [
            3341
          ],
          [
            3342
          ]
        ],
        [
          [
            3343
          ],
          [
            3344,
            3345
          ]
        ]
      ],
      "ordinal": 80,
      "paragraph_ordinals": [
        3316,
        3317,
        3318,
        3319,
        3320,
        3321,
        3322,
        3323,
        3324,
        3325,
        3326,
        3327,
        3328,
        3329,
        3330,
        3331,
        3332,
        3333,
        3334,
        3335,
        3336,
        3337,
        3338,
        3339,
        3340,
        3341,
        3342,
        3343,
        3344,
        3345
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV04-R0-generation-typing；\nclaim_level=descriptive_classification；\nwhen=GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=分别登记候选生成条件、候选生成主体与候选生成事件，不将三者互相替代。；\nresult_ceiling=只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。\n2. route_id=HV04-R1-generation-mechanism；\nclaim_level=mechanism_explanation；\nwhen=预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；\nadditional_inferential_requires=G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定尺度、窗口和通道内的候选生成机制及其GC、GS、GE分型。；\nresult_ceiling=不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 条件性生成路径2. 有主体或无主体生成"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 技术或危机具有意图\n2. 生成主体自动拥有持续授权"
        ]
      ]
    },
    {
      "anchor": "V82-T081",
      "cell_paragraph_ordinals": [
        [
          [
            3347
          ],
          [
            3348
          ]
        ],
        [
          [
            3349
          ],
          [
            3350
          ]
        ],
        [
          [
            3351
          ],
          [
            3352
          ]
        ],
        [
          [
            3353
          ],
          [
            3354
          ]
        ],
        [
          [
            3355
          ],
          [
            3356,
            3357,
            3358,
            3359
          ]
        ],
        [
          [
            3360
          ],
          [
            3361
          ]
        ],
        [
          [
            3362
          ],
          [
            3363
          ]
        ],
        [
          [
            3364
          ],
          [
            3365
          ]
        ]
      ],
      "ordinal": 81,
      "paragraph_ordinals": [
        3347,
        3348,
        3349,
        3350,
        3351,
        3352,
        3353,
        3354,
        3355,
        3356,
        3357,
        3358,
        3359,
        3360,
        3361,
        3362,
        3363,
        3364,
        3365
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：条件暴露、主体行动与生成事件单元，各自个案总体、分布及聚合规则；X=空间范围：生成现场、组织或平台边界、扩散区域与跨域环境；T=时间跨度：条件积累期、主体行动窗、事件时点与扩散时滞；O=组织层级：行动角色、生成团队、组织、制度至治理生态；C=因果层次：生成事件、主体—条件互动机制、中观生成结构、制度安排与系统条件；R=观察分辨率：原始条件行动事件、生成序列、个案、结果分布、转移指标与摘要，并登记压缩损失；I=影响范围：直接生成参与者、承接者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：条件传播、主体协作、事件扩散与涌现连接；J=管辖与授权范围：生成识别、启动改变、资源投入及扩散处置分别登记授权；GC、GS、GE分别登记尺度"
        ],
        [
          "有效对象（effective_object）",
          "形成可检测状态转移的条件、主体与事件组合"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. GC、GS、GE强类型分离"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 新单位与总体\n2. 代表关系\n3. 责任类型\n4. 外部影响"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 生成主体、条件与事件可随尺度改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 没有新状态形成或生成主张的稳定描述"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 把条件或事件升格为有意图主体"
        ]
      ]
    },
    {
      "anchor": "V82-T082",
      "cell_paragraph_ordinals": [
        [
          [
            3367
          ],
          [
            3368
          ]
        ],
        [
          [
            3369
          ],
          [
            3370,
            3371,
            3372,
            3373,
            3374
          ]
        ],
        [
          [
            3375
          ],
          [
            3376,
            3377,
            3378,
            3379
          ]
        ],
        [
          [
            3380
          ],
          [
            3381,
            3382,
            3383,
            3384
          ]
        ],
        [
          [
            3385
          ],
          [
            3386
          ]
        ],
        [
          [
            3387
          ],
          [
            3388
          ]
        ],
        [
          [
            3389
          ],
          [
            3390
          ]
        ],
        [
          [
            3391
          ],
          [
            3392
          ]
        ],
        [
          [
            3393
          ],
          [
            3394
          ]
        ],
        [
          [
            3395
          ],
          [
            3396,
            3397,
            3398,
            3399
          ]
        ]
      ],
      "ordinal": 82,
      "paragraph_ordinals": [
        3367,
        3368,
        3369,
        3370,
        3371,
        3372,
        3373,
        3374,
        3375,
        3376,
        3377,
        3378,
        3379,
        3380,
        3381,
        3382,
        3383,
        3384,
        3385,
        3386,
        3387,
        3388,
        3389,
        3390,
        3391,
        3392,
        3393,
        3394,
        3395,
        3396,
        3397,
        3398,
        3399
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 潜在\n2. 触发\n3. 形成\n4. 中断\n5. 扩散"
        ],
        [
          "可观测项（observables）",
          "1. 候选条件出现、改变或移除的时间记录\n2. 生成主体的能力、授权、决策与实际行动\n3. 生成事件前后预注册状态转移\n4. 无主体涌现时局部互动与总体结果的桥接记录"
        ],
        [
          "证据要求（evidence）",
          "1. 启动记录\n2. 条件窗口\n3. 主体行动\n4. 无主体互动机制"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 指向锚点2. 资源与制度条件3. 因果合同"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 承接需求2. 状态转移3. 责任链起点"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记条件积累、触发事件与形成时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录共同生成、无主体涌现和不可识别主体"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "被遗漏的非正式启动者与受影响位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 启动者\n2. 承接者\n3. 受益者\n4. 受影响者"
        ]
      ]
    },
    {
      "anchor": "V82-T083",
      "cell_paragraph_ordinals": [
        [
          [
            3401
          ],
          [
            3402
          ]
        ],
        [
          [
            3403
          ],
          [
            3404,
            3405,
            3406,
            3407
          ]
        ],
        [
          [
            3408
          ],
          [
            3409
          ]
        ],
        [
          [
            3410
          ],
          [
            3411
          ]
        ],
        [
          [
            3412
          ],
          [
            3413
          ]
        ],
        [
          [
            3414
          ],
          [
            3415
          ]
        ],
        [
          [
            3416
          ],
          [
            3417,
            3418
          ]
        ],
        [
          [
            3419
          ],
          [
            3420
          ]
        ],
        [
          [
            3421
          ],
          [
            3422
          ]
        ]
      ],
      "ordinal": 83,
      "paragraph_ordinals": [
        3401,
        3402,
        3403,
        3404,
        3405,
        3406,
        3407,
        3408,
        3409,
        3410,
        3411,
        3412,
        3413,
        3414,
        3415,
        3416,
        3417,
        3418,
        3419,
        3420,
        3421,
        3422
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 启动者\n2. 程序\n3. 技术设施\n4. 关系网络"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 实际行动者2. 决策者3. 授权者"
        ],
        [
          "规范地位（normative_status）",
          "生成事实不证明正当或责任完整"
        ],
        [
          "判断上限（judgment_ceiling）",
          "机制链完整时至解释级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成GC、GS、GE候选分型、状态转移描述与补证需求，不授权启动、扩散或停止生成过程；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 技术条件被错误描述成具有目标的生成主体\n2. 无统一发起者的涌现过程被强行归因给一个可见人物"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，被归为生成主体者可经安全可达、反报复通道挑战意图、角色与授权归因，并触发与原分型或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正GC、GS、GE类型，实际移除错误意图或责任归因及其下游效力，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T084",
      "cell_paragraph_ordinals": [
        [
          [
            3425
          ],
          [
            3426
          ]
        ],
        [
          [
            3427
          ],
          [
            3428
          ]
        ],
        [
          [
            3429
          ],
          [
            3430
          ]
        ],
        [
          [
            3431
          ],
          [
            3432
          ]
        ],
        [
          [
            3433
          ],
          [
            3434
          ]
        ],
        [
          [
            3435
          ],
          [
            3436
          ]
        ],
        [
          [
            3437
          ],
          [
            3438
          ]
        ],
        [
          [
            3439
          ],
          [
            3440
          ]
        ],
        [
          [
            3441
          ],
          [
            3442
          ]
        ]
      ],
      "ordinal": 84,
      "paragraph_ordinals": [
        3425,
        3426,
        3427,
        3428,
        3429,
        3430,
        3431,
        3432,
        3433,
        3434,
        3435,
        3436,
        3437,
        3438,
        3439,
        3440,
        3441,
        3442
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV05"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV05"
        ],
        [
          "名称（name）",
          "行动承接层"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。"
        ],
        [
          "适用范围（scope）",
          "需要持续行动、维护、照护或执行的人类结构"
        ],
        [
          "暂停条件（pause_condition）",
          "低权限执行者被默认归为主要责任人或承接能力被当作义务"
        ]
      ]
    },
    {
      "anchor": "V82-T085",
      "cell_paragraph_ordinals": [
        [
          [
            3444
          ],
          [
            3445
          ]
        ],
        [
          [
            3446
          ],
          [
            3447
          ]
        ],
        [
          [
            3448
          ],
          [
            3449
          ]
        ],
        [
          [
            3450
          ],
          [
            3451
          ]
        ],
        [
          [
            3452
          ],
          [
            3453
          ]
        ],
        [
          [
            3454
          ],
          [
            3455,
            3456,
            3457,
            3458,
            3459,
            3460,
            3461,
            3462,
            3463,
            3464,
            3465,
            3466,
            3467,
            3468,
            3469,
            3470,
            3471,
            3472,
            3473,
            3474,
            3475,
            3476,
            3477,
            3478,
            3479,
            3480,
            3481,
            3482
          ]
        ],
        [
          [
            3483
          ],
          [
            3484
          ]
        ],
        [
          [
            3485
          ],
          [
            3486,
            3487,
            3488
          ]
        ]
      ],
      "ordinal": 85,
      "paragraph_ordinals": [
        3444,
        3445,
        3446,
        3447,
        3448,
        3449,
        3450,
        3451,
        3452,
        3453,
        3454,
        3455,
        3456,
        3457,
        3458,
        3459,
        3460,
        3461,
        3462,
        3463,
        3464,
        3465,
        3466,
        3467,
        3468,
        3469,
        3470,
        3471,
        3472,
        3473,
        3474,
        3475,
        3476,
        3477,
        3478,
        3479,
        3480,
        3481,
        3482,
        3483,
        3484,
        3485,
        3486,
        3487,
        3488
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "1. H2"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV05-R0-carrier-responsibility-split；\nclaim_level=descriptive_classification；\nwhen=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；\nresult_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。\n2. route_id=HV05-R1-functional-carrier-effect；\nclaim_level=conditional_effect；\nwhen=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；\nadditional_inferential_requires=G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；\nresult_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。\n3. route_id=HV05-R2-intertemporal-reproduction；\nclaim_level=intertemporal_explanation；\nwhen=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；\nadditional_inferential_requires=G2-instance、G3-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定窗口与载体内的跨期承接或再生产候选。；\nresult_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。\n4. route_id=HV05-R3-historical-carrier-trace；\nclaim_level=descriptive_classification；\nwhen=H5-instance对唯一预选的具体载体与持久判据取得supported。；\nadditional_inferential_requires=H5-instance；\nadditional_protocol_requires=E4；\nallowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；\nresult_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 承接缺口2. 任务资源错配3. 责任分流"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 最可见者等于主要责任人\n2. 能承担所以应承担\n3. 非人载体承担责任"
        ]
      ]
    },
    {
      "anchor": "V82-T086",
      "cell_paragraph_ordinals": [
        [
          [
            3490
          ],
          [
            3491
          ]
        ],
        [
          [
            3492
          ],
          [
            3493
          ]
        ],
        [
          [
            3494
          ],
          [
            3495
          ]
        ],
        [
          [
            3496
          ],
          [
            3497,
            3498,
            3499
          ]
        ],
        [
          [
            3500
          ],
          [
            3501,
            3502,
            3503,
            3504
          ]
        ],
        [
          [
            3505
          ],
          [
            3506
          ]
        ],
        [
          [
            3507
          ],
          [
            3508
          ]
        ],
        [
          [
            3509
          ],
          [
            3510
          ]
        ]
      ],
      "ordinal": 86,
      "paragraph_ordinals": [
        3490,
        3491,
        3492,
        3493,
        3494,
        3495,
        3496,
        3497,
        3498,
        3499,
        3500,
        3501,
        3502,
        3503,
        3504,
        3505,
        3506,
        3507,
        3508,
        3509,
        3510
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度"
        ],
        [
          "有效对象（effective_object）",
          "实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. CV不等于RS\n2. 成本与受益分别登记\n3. 停止权"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 任务聚合\n2. 代表和委托\n3. 六类责任\n4. 外部成本"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 承接载体和责任主体可随层级改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无主体行动、责任或维护要求的非人过程"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 个体承接直接等于组织责任"
        ]
      ]
    },
    {
      "anchor": "V82-T087",
      "cell_paragraph_ordinals": [
        [
          [
            3512
          ],
          [
            3513
          ]
        ],
        [
          [
            3514
          ],
          [
            3515,
            3516,
            3517,
            3518,
            3519
          ]
        ],
        [
          [
            3520
          ],
          [
            3521,
            3522,
            3523,
            3524
          ]
        ],
        [
          [
            3525
          ],
          [
            3526,
            3527,
            3528,
            3529
          ]
        ],
        [
          [
            3530
          ],
          [
            3531
          ]
        ],
        [
          [
            3532
          ],
          [
            3533
          ]
        ],
        [
          [
            3534
          ],
          [
            3535
          ]
        ],
        [
          [
            3536
          ],
          [
            3537
          ]
        ],
        [
          [
            3538
          ],
          [
            3539
          ]
        ],
        [
          [
            3540
          ],
          [
            3541,
            3542,
            3543,
            3544
          ]
        ]
      ],
      "ordinal": 87,
      "paragraph_ordinals": [
        3512,
        3513,
        3514,
        3515,
        3516,
        3517,
        3518,
        3519,
        3520,
        3521,
        3522,
        3523,
        3524,
        3525,
        3526,
        3527,
        3528,
        3529,
        3530,
        3531,
        3532,
        3533,
        3534,
        3535,
        3536,
        3537,
        3538,
        3539,
        3540,
        3541,
        3542,
        3543,
        3544
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 充足\n2. 脆弱\n3. 过载\n4. 断裂\n5. 替代"
        ],
        [
          "可观测项（observables）",
          "1. 任务实际执行、维护、记录与修复日志\n2. 资源、容量、时间和成本流向\n3. 停止权、替代安排与承接转移记录\n4. 决策、授权、监督、受益与补救依据"
        ],
        [
          "证据要求（evidence）",
          "1. 任务流\n2. 工时与资源\n3. 维护记录\n4. 停止和拒绝记录"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 生成需求2. 资源3. 授权4. 角色"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 实现状态转移2. 成本分布3. 结构负荷"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记排班、维护周期、积压与恢复时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录隐性劳动、非正式照护和边界外成本"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "低权限、非正式与不可退出承接者"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 承接者\n2. 受益者\n3. 被服务者\n4. 替代者"
        ]
      ]
    },
    {
      "anchor": "V82-T088",
      "cell_paragraph_ordinals": [
        [
          [
            3546
          ],
          [
            3547
          ]
        ],
        [
          [
            3548
          ],
          [
            3549,
            3550,
            3551,
            3552,
            3553
          ]
        ],
        [
          [
            3554
          ],
          [
            3555,
            3556,
            3557,
            3558,
            3559,
            3560
          ]
        ],
        [
          [
            3561
          ],
          [
            3562
          ]
        ],
        [
          [
            3563
          ],
          [
            3564
          ]
        ],
        [
          [
            3565
          ],
          [
            3566
          ]
        ],
        [
          [
            3567
          ],
          [
            3568,
            3569
          ]
        ],
        [
          [
            3570
          ],
          [
            3571
          ]
        ],
        [
          [
            3572
          ],
          [
            3573
          ]
        ]
      ],
      "ordinal": 88,
      "paragraph_ordinals": [
        3546,
        3547,
        3548,
        3549,
        3550,
        3551,
        3552,
        3553,
        3554,
        3555,
        3556,
        3557,
        3558,
        3559,
        3560,
        3561,
        3562,
        3563,
        3564,
        3565,
        3566,
        3567,
        3568,
        3569,
        3570,
        3571,
        3572,
        3573
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 人员\n2. 岗位\n3. 程序\n4. 设施\n5. 制度"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 行为责任者\n2. 决策责任者\n3. 授权责任者\n4. 监督责任者\n5. 受益责任者\n6. 补救责任者"
        ],
        [
          "规范地位（normative_status）",
          "承接事实不产生继续承担义务"
        ],
        [
          "判断上限（judgment_ceiling）",
          "资源与责任链完整时至诊断级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 最可见的低权限执行者不是决策、授权或受益责任主体\n2. 自动化设施承担传导任务但不能承担道德或法律责任"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T089",
      "cell_paragraph_ordinals": [
        [
          [
            3576
          ],
          [
            3577
          ]
        ],
        [
          [
            3578
          ],
          [
            3579
          ]
        ],
        [
          [
            3580
          ],
          [
            3581
          ]
        ],
        [
          [
            3582
          ],
          [
            3583
          ]
        ],
        [
          [
            3584
          ],
          [
            3585
          ]
        ],
        [
          [
            3586
          ],
          [
            3587
          ]
        ],
        [
          [
            3588
          ],
          [
            3589
          ]
        ],
        [
          [
            3590
          ],
          [
            3591
          ]
        ],
        [
          [
            3592
          ],
          [
            3593
          ]
        ]
      ],
      "ordinal": 89,
      "paragraph_ordinals": [
        3576,
        3577,
        3578,
        3579,
        3580,
        3581,
        3582,
        3583,
        3584,
        3585,
        3586,
        3587,
        3588,
        3589,
        3590,
        3591,
        3592,
        3593
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV06"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV06"
        ],
        [
          "名称（name）",
          "动力—承接链"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "从指向、生成到执行、维护与偿付的链条必须逐段登记通道、资源、成本、责任和时滞。"
        ],
        [
          "适用范围（scope）",
          "人类集体行动、项目、组织与制度运行"
        ],
        [
          "暂停条件（pause_condition）",
          "用热情、愿景或命令替代承接与偿付证据"
        ]
      ]
    },
    {
      "anchor": "V82-T090",
      "cell_paragraph_ordinals": [
        [
          [
            3595
          ],
          [
            3596
          ]
        ],
        [
          [
            3597
          ],
          [
            3598
          ]
        ],
        [
          [
            3599
          ],
          [
            3600
          ]
        ],
        [
          [
            3601
          ],
          [
            3602
          ]
        ],
        [
          [
            3603
          ],
          [
            3604
          ]
        ],
        [
          [
            3605
          ],
          [
            3606,
            3607,
            3608,
            3609,
            3610,
            3611,
            3612,
            3613,
            3614,
            3615,
            3616,
            3617,
            3618,
            3619,
            3620,
            3621,
            3622,
            3623,
            3624,
            3625,
            3626
          ]
        ],
        [
          [
            3627
          ],
          [
            3628
          ]
        ],
        [
          [
            3629
          ],
          [
            3630,
            3631,
            3632
          ]
        ]
      ],
      "ordinal": 90,
      "paragraph_ordinals": [
        3595,
        3596,
        3597,
        3598,
        3599,
        3600,
        3601,
        3602,
        3603,
        3604,
        3605,
        3606,
        3607,
        3608,
        3609,
        3610,
        3611,
        3612,
        3613,
        3614,
        3615,
        3616,
        3617,
        3618,
        3619,
        3620,
        3621,
        3622,
        3623,
        3624,
        3625,
        3626,
        3627,
        3628,
        3629,
        3630,
        3631,
        3632
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV06-R0-segment-map；\nclaim_level=descriptive_classification；\nwhen=至少一个链段的输入、输出、时延、损耗、中断、资源、成本与边界可观察。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记局部链段、缺失桥、时滞、损耗、中断点与成本位置。；\nresult_ceiling=不得由单一链段或动力语言宣称完整链条或有效通道。\n2. route_id=HV06-R1-complete-chain-composition；\nclaim_level=descriptive_classification；\nwhen=指向、生成与承接三个接口记录可在同一对象、尺度、窗口与量的映射中逐段连接。；\nadditional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记完整候选动力—承接链及逐段证据覆盖。；\nresult_ceiling=只到候选链条组成；接口记录齐全不等于各链段具有因果效力。\n3. route_id=HV06-R2-effective-channel；\nclaim_level=mechanism_explanation；\nwhen=完整候选链已组成，且符合资格的G2-instance逐段识别指定通道对目标转移的效应。；\nadditional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05、G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记已检验链段和窗口内的有效动力—承接通道、损耗与中断机制。；\nresult_ceiling=不得从一次贯通推出跨期再生产、责任、正当性或行动授权。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 链条瓶颈2. 动力与承接脱节3. 隐性偿付"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 动力强等于可持续\n2. 失败归因意愿不足\n3. 承接者应自行补洞"
        ]
      ]
    },
    {
      "anchor": "V82-T091",
      "cell_paragraph_ordinals": [
        [
          [
            3634
          ],
          [
            3635
          ]
        ],
        [
          [
            3636
          ],
          [
            3637
          ]
        ],
        [
          [
            3638
          ],
          [
            3639
          ]
        ],
        [
          [
            3640
          ],
          [
            3641
          ]
        ],
        [
          [
            3642
          ],
          [
            3643,
            3644,
            3645,
            3646
          ]
        ],
        [
          [
            3647
          ],
          [
            3648
          ]
        ],
        [
          [
            3649
          ],
          [
            3650
          ]
        ],
        [
          [
            3651
          ],
          [
            3652
          ]
        ]
      ],
      "ordinal": 91,
      "paragraph_ordinals": [
        3634,
        3635,
        3636,
        3637,
        3638,
        3639,
        3640,
        3641,
        3642,
        3643,
        3644,
        3645,
        3646,
        3647,
        3648,
        3649,
        3650,
        3651,
        3652
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单个链节事件、链条个案、同类链总体、输入输出分布及聚合规则；X=空间范围：行动现场、项目或组织边界、数字协作空间与跨域外溢；T=时间跨度：启动、维持、中断、恢复窗口及跨期周期；O=组织层级：发起角色、执行团队、组织、制度至治理生态；C=因果层次：链节事件、动力—资源—任务互动机制、中观承接链、制度安排与系统条件；R=观察分辨率：原始任务资源记录、链节序列、链条个案、损耗分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接发起与承接位置、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖链、替代路径、瓶颈、反馈连接与跨域桥接；J=管辖与授权范围：目标采用、任务分配、资源投入、停止与试验分别登记授权；逐段标明跨轴位置"
        ],
        [
          "有效对象（effective_object）",
          "把指向和生成转为持续行动的可追踪链条"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 指向、生成、承接、资源、成本和责任链"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 跨层桥接\n2. 聚合损失\n3. 责任继承\n4. 保护底板"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 节点、通道和瓶颈可随组织尺度改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无意向动力与人类承接的非人过程"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 局部动力或单一节点直接代表完整链条"
        ]
      ]
    },
    {
      "anchor": "V82-T092",
      "cell_paragraph_ordinals": [
        [
          [
            3654
          ],
          [
            3655
          ]
        ],
        [
          [
            3656
          ],
          [
            3657,
            3658,
            3659,
            3660,
            3661
          ]
        ],
        [
          [
            3662
          ],
          [
            3663,
            3664,
            3665,
            3666
          ]
        ],
        [
          [
            3667
          ],
          [
            3668,
            3669,
            3670,
            3671
          ]
        ],
        [
          [
            3672
          ],
          [
            3673
          ]
        ],
        [
          [
            3674
          ],
          [
            3675
          ]
        ],
        [
          [
            3676
          ],
          [
            3677
          ]
        ],
        [
          [
            3678
          ],
          [
            3679
          ]
        ],
        [
          [
            3680
          ],
          [
            3681
          ]
        ],
        [
          [
            3682
          ],
          [
            3683,
            3684,
            3685,
            3686
          ]
        ]
      ],
      "ordinal": 92,
      "paragraph_ordinals": [
        3654,
        3655,
        3656,
        3657,
        3658,
        3659,
        3660,
        3661,
        3662,
        3663,
        3664,
        3665,
        3666,
        3667,
        3668,
        3669,
        3670,
        3671,
        3672,
        3673,
        3674,
        3675,
        3676,
        3677,
        3678,
        3679,
        3680,
        3681,
        3682,
        3683,
        3684,
        3685,
        3686
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 贯通\n2. 迟滞\n3. 过载\n4. 断裂\n5. 替代"
        ],
        [
          "可观测项（observables）",
          "1. 锚点转化为任务、预算、规则或排程的记录\n2. 每段输入输出、时延、损耗与中断点\n3. 承接者容量、停止与替代路径变化\n4. 链条输出对目标结果的实际贡献"
        ],
        [
          "证据要求（evidence）",
          "1. 资源流\n2. 任务与维护记录\n3. 偿付与成本\n4. 时滞"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 指向锚点2. 生成节点3. 承接层"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 行动结果2. 负荷3. 反馈与演化痕迹"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "逐段登记启动、传导、维护和偿付时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录断点、替代通道与边界外偿付"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "非正式、低可见和跨组织承接位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 发起者\n2. 承接者\n3. 受益者\n4. 成本承担者"
        ]
      ]
    },
    {
      "anchor": "V82-T093",
      "cell_paragraph_ordinals": [
        [
          [
            3688
          ],
          [
            3689
          ]
        ],
        [
          [
            3690
          ],
          [
            3691,
            3692,
            3693,
            3694
          ]
        ],
        [
          [
            3695
          ],
          [
            3696
          ]
        ],
        [
          [
            3697
          ],
          [
            3698
          ]
        ],
        [
          [
            3699
          ],
          [
            3700
          ]
        ],
        [
          [
            3701
          ],
          [
            3702
          ]
        ],
        [
          [
            3703
          ],
          [
            3704,
            3705
          ]
        ],
        [
          [
            3706
          ],
          [
            3707
          ]
        ],
        [
          [
            3708
          ],
          [
            3709
          ]
        ]
      ],
      "ordinal": 93,
      "paragraph_ordinals": [
        3688,
        3689,
        3690,
        3691,
        3692,
        3693,
        3694,
        3695,
        3696,
        3697,
        3698,
        3699,
        3700,
        3701,
        3702,
        3703,
        3704,
        3705,
        3706,
        3707,
        3708,
        3709
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 人员与岗位\n2. 程序\n3. 预算\n4. 基础设施"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 各节点行为、决策、授权、监督与补救责任者"
        ],
        [
          "规范地位（normative_status）",
          "链条有效不证明目标正当"
        ],
        [
          "判断上限（judgment_ceiling）",
          "全链证据充分时至解释或诊断级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成链条连通、时滞、损耗、中断、成本与承接需求描述，不授权减载、资源调整或试验；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 强烈愿景和集中动员没有持续资源、维护或偿付\n2. 表面贯通的链条把关键成本转移给边界外承接者"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，链上承接或受影响位置可经安全可达、反报复通道挑战资源、成本与链条归因，并触发与原链条判断或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销整体链条归因及其下游效力、恢复为节点级描述与未决状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T094",
      "cell_paragraph_ordinals": [
        [
          [
            3712
          ],
          [
            3713
          ]
        ],
        [
          [
            3714
          ],
          [
            3715
          ]
        ],
        [
          [
            3716
          ],
          [
            3717
          ]
        ],
        [
          [
            3718
          ],
          [
            3719
          ]
        ],
        [
          [
            3720
          ],
          [
            3721
          ]
        ],
        [
          [
            3722
          ],
          [
            3723
          ]
        ],
        [
          [
            3724
          ],
          [
            3725
          ]
        ],
        [
          [
            3726
          ],
          [
            3727
          ]
        ],
        [
          [
            3728
          ],
          [
            3729
          ]
        ]
      ],
      "ordinal": 94,
      "paragraph_ordinals": [
        3712,
        3713,
        3714,
        3715,
        3716,
        3717,
        3718,
        3719,
        3720,
        3721,
        3722,
        3723,
        3724,
        3725,
        3726,
        3727,
        3728,
        3729
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV07"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV07"
        ],
        [
          "名称（name）",
          "反馈写回"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "申诉、审计和反馈只有改变记录、规则、资源、角色、责任、记忆或停止条件时才构成人类制度写回。"
        ],
        [
          "适用范围（scope）",
          "具有反馈、申诉、审计或治理程序的人类结构"
        ],
        [
          "暂停条件（pause_condition）",
          "只有接收回执、表态或发布而无状态更新"
        ]
      ]
    },
    {
      "anchor": "V82-T095",
      "cell_paragraph_ordinals": [
        [
          [
            3731
          ],
          [
            3732
          ]
        ],
        [
          [
            3733
          ],
          [
            3734
          ]
        ],
        [
          [
            3735
          ],
          [
            3736
          ]
        ],
        [
          [
            3737
          ],
          [
            3738
          ]
        ],
        [
          [
            3739
          ],
          [
            3740
          ]
        ],
        [
          [
            3741
          ],
          [
            3742,
            3743,
            3744,
            3745,
            3746,
            3747,
            3748,
            3749,
            3750,
            3751,
            3752,
            3753,
            3754,
            3755,
            3756,
            3757,
            3758,
            3759,
            3760,
            3761,
            3762
          ]
        ],
        [
          [
            3763
          ],
          [
            3764
          ]
        ],
        [
          [
            3765
          ],
          [
            3766,
            3767,
            3768
          ]
        ]
      ],
      "ordinal": 95,
      "paragraph_ordinals": [
        3731,
        3732,
        3733,
        3734,
        3735,
        3736,
        3737,
        3738,
        3739,
        3740,
        3741,
        3742,
        3743,
        3744,
        3745,
        3746,
        3747,
        3748,
        3749,
        3750,
        3751,
        3752,
        3753,
        3754,
        3755,
        3756,
        3757,
        3758,
        3759,
        3760,
        3761,
        3762,
        3763,
        3764,
        3765,
        3766,
        3767,
        3768
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "1. D2"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "1. H3"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV07-R0-writeback-classification；\nclaim_level=descriptive_classification；\nwhen=输入通道、回执、字段前后版本、执行记录、生效时间、持续时间及停止或回滚状态可分别检查。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=区分未提交、已提交、已受理、字段改变、已执行、持续或失效的写回状态。；\nresult_ceiling=只有字段改变且实际执行才称制度性写回；一次写回不称学习。\n2. route_id=HV07-R1-causal-feedback；\nclaim_level=mechanism_explanation；\nwhen=符合资格的G2-instance显示制度返回通道相对无返回或阻断条件改变预选后续状态或转移。；\nadditional_inferential_requires=G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定字段、通道和窗口内的有效反馈与制度写回效应。；\nresult_ceiling=不得从反馈存在推出学习、长期修复、正当性或授权扩大。\n3. route_id=HV07-R2-feedback-mediated-learning；\nclaim_level=intertemporal_explanation；\nwhen=有效反馈已有G2-instance支持，且G3-instance显示可保留更新在重复轮次对预定任务提供历史条件增量。；\nadditional_inferential_requires=G2-instance、G3-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记限定任务、轮次和窗口内的反馈介导学习候选。；\nresult_ceiling=不得称整体制度已经学习、修复完成或价值方向正确。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 有效写回、阻塞写回与表面反馈"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 有渠道即会学习\n2. 一次更新即长期修复\n3. 沉默即同意"
        ]
      ]
    },
    {
      "anchor": "V82-T096",
      "cell_paragraph_ordinals": [
        [
          [
            3770
          ],
          [
            3771
          ]
        ],
        [
          [
            3772
          ],
          [
            3773
          ]
        ],
        [
          [
            3774
          ],
          [
            3775
          ]
        ],
        [
          [
            3776
          ],
          [
            3777
          ]
        ],
        [
          [
            3778
          ],
          [
            3779,
            3780,
            3781,
            3782
          ]
        ],
        [
          [
            3783
          ],
          [
            3784
          ]
        ],
        [
          [
            3785
          ],
          [
            3786
          ]
        ],
        [
          [
            3787
          ],
          [
            3788
          ]
        ]
      ],
      "ordinal": 96,
      "paragraph_ordinals": [
        3770,
        3771,
        3772,
        3773,
        3774,
        3775,
        3776,
        3777,
        3778,
        3779,
        3780,
        3781,
        3782,
        3783,
        3784,
        3785,
        3786,
        3787,
        3788
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次反馈或申诉、写回个案、反馈总体、受理执行分布及聚合规则；X=空间范围：提交渠道、组织或平台边界、制度辖区与跨域申诉范围；T=时间跨度：提交、受理、字段变化、执行、持续与复核时滞；O=组织层级：反馈角色、受理团队、组织、制度至治理生态；C=因果层次：反馈事件、写回互动机制、中观程序结构、制度规则与系统条件；R=观察分辨率：原始反馈、处理序列、写回个案、结果分布、时效指标与摘要，并登记压缩损失；I=影响范围：直接申诉人与承接者、间接受影响者、二阶制度后果、跨域与代际影响；N=网络拓扑范围：反馈通道、受理节点、复核路径、阻塞点与跨层连接；J=管辖与授权范围：受理、字段修改、执行、停止、回滚与补救分别登记授权；登记跨层路径"
        ],
        [
          "有效对象（effective_object）",
          "改变后续制度状态或转移的返回通道"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 反馈来源、通道、写回字段和后续变化"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 反馈代表性\n2. 跨层写回路径\n3. 聚合损失\n4. 外部复核"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 写回载体、时滞和责任主体可改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无记录、规则、资源、角色或停止条件的过程"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 个案反馈直接代表总体意见"
        ]
      ]
    },
    {
      "anchor": "V82-T097",
      "cell_paragraph_ordinals": [
        [
          [
            3790
          ],
          [
            3791
          ]
        ],
        [
          [
            3792
          ],
          [
            3793,
            3794,
            3795,
            3796,
            3797
          ]
        ],
        [
          [
            3798
          ],
          [
            3799,
            3800,
            3801,
            3802
          ]
        ],
        [
          [
            3803
          ],
          [
            3804,
            3805,
            3806,
            3807
          ]
        ],
        [
          [
            3808
          ],
          [
            3809,
            3810,
            3811,
            3812
          ]
        ],
        [
          [
            3813
          ],
          [
            3814
          ]
        ],
        [
          [
            3815
          ],
          [
            3816
          ]
        ],
        [
          [
            3817
          ],
          [
            3818
          ]
        ],
        [
          [
            3819
          ],
          [
            3820
          ]
        ],
        [
          [
            3821
          ],
          [
            3822,
            3823,
            3824,
            3825
          ]
        ]
      ],
      "ordinal": 97,
      "paragraph_ordinals": [
        3790,
        3791,
        3792,
        3793,
        3794,
        3795,
        3796,
        3797,
        3798,
        3799,
        3800,
        3801,
        3802,
        3803,
        3804,
        3805,
        3806,
        3807,
        3808,
        3809,
        3810,
        3811,
        3812,
        3813,
        3814,
        3815,
        3816,
        3817,
        3818,
        3819,
        3820,
        3821,
        3822,
        3823,
        3824,
        3825
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 到达\n2. 受理\n3. 写回\n4. 阻塞\n5. 失真"
        ],
        [
          "可观测项（observables）",
          "1. 反馈或申诉的提交与受理凭证\n2. 记录、规则、资源、角色、责任或停止条件的版本差异\n3. 变更的执行记录、生效时间与持续时间\n4. 复核、撤销、补救及后续状态变化"
        ],
        [
          "证据要求（evidence）",
          "1. 反馈原文\n2. 受理轨迹\n3. 字段版本\n4. 后续规则或资源变化"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 反馈来源\n2. 安全通道\n3. 责任人\n4. 复核程序"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 记录、规则、资源、角色、责任、记忆或停止条件更新"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记提交、受理、决定、执行和复审时限"
        ],
        [
          "不确定性（uncertainty）",
          "记录未达反馈、保护性匿名与不可见处理"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "无法安全提交、受反报复威胁或无数字接入的位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 提交者\n2. 被评价者\n3. 执行者\n4. 制度受益者"
        ]
      ]
    },
    {
      "anchor": "V82-T098",
      "cell_paragraph_ordinals": [
        [
          [
            3827
          ],
          [
            3828
          ]
        ],
        [
          [
            3829
          ],
          [
            3830,
            3831,
            3832,
            3833,
            3834
          ]
        ],
        [
          [
            3835
          ],
          [
            3836,
            3837,
            3838,
            3839
          ]
        ],
        [
          [
            3840
          ],
          [
            3841
          ]
        ],
        [
          [
            3842
          ],
          [
            3843
          ]
        ],
        [
          [
            3844
          ],
          [
            3845
          ]
        ],
        [
          [
            3846
          ],
          [
            3847,
            3848
          ]
        ],
        [
          [
            3849
          ],
          [
            3850
          ]
        ],
        [
          [
            3851
          ],
          [
            3852
          ]
        ]
      ],
      "ordinal": 98,
      "paragraph_ordinals": [
        3827,
        3828,
        3829,
        3830,
        3831,
        3832,
        3833,
        3834,
        3835,
        3836,
        3837,
        3838,
        3839,
        3840,
        3841,
        3842,
        3843,
        3844,
        3845,
        3846,
        3847,
        3848,
        3849,
        3850,
        3851,
        3852
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 申诉系统\n2. 审计程序\n3. 会议记录\n4. 规则库\n5. 责任链"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 受理者\n2. 决策者\n3. 写回执行者\n4. 监督者"
        ],
        [
          "规范地位（normative_status）",
          "反馈有效性与反馈内容正当性分别判断"
        ],
        [
          "判断上限（judgment_ceiling）",
          "确认写回字段和后续变化时至解释级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成受理、字段变化、执行、持续时间与写回缺口描述，以及复核或程序修复需求，不授权改写记录规则、执行修复或关闭申诉；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 申诉获得接收回执但记录、规则、资源和停止条件均未改变\n2. 审计报告被发布却没有责任人、时限或后续状态更新"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，反馈提交者可经安全可达、反报复通道要求状态、时限、责任人与写回结果，并触发与原受理、写回或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误更新，实际恢复先前记录、规则、资源、角色或停止条件状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T099",
      "cell_paragraph_ordinals": [
        [
          [
            3855
          ],
          [
            3856
          ]
        ],
        [
          [
            3857
          ],
          [
            3858
          ]
        ],
        [
          [
            3859
          ],
          [
            3860
          ]
        ],
        [
          [
            3861
          ],
          [
            3862
          ]
        ],
        [
          [
            3863
          ],
          [
            3864
          ]
        ],
        [
          [
            3865
          ],
          [
            3866
          ]
        ],
        [
          [
            3867
          ],
          [
            3868
          ]
        ],
        [
          [
            3869
          ],
          [
            3870
          ]
        ],
        [
          [
            3871
          ],
          [
            3872
          ]
        ]
      ],
      "ordinal": 99,
      "paragraph_ordinals": [
        3855,
        3856,
        3857,
        3858,
        3859,
        3860,
        3861,
        3862,
        3863,
        3864,
        3865,
        3866,
        3867,
        3868,
        3869,
        3870,
        3871,
        3872
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV08"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV08"
        ],
        [
          "名称（name）",
          "条件势场"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "资源、制度、关系、权力、安全、指标、平台与历史条件只有通过可检测机制改变人类行动概率或约束时进入解释。"
        ],
        [
          "适用范围（scope）",
          "人类行动受情境、制度与权力位置影响的场景"
        ],
        [
          "暂停条件（pause_condition）",
          "势场被当作万能背景、意图主体或道德标签"
        ]
      ]
    },
    {
      "anchor": "V82-T100",
      "cell_paragraph_ordinals": [
        [
          [
            3874
          ],
          [
            3875
          ]
        ],
        [
          [
            3876
          ],
          [
            3877
          ]
        ],
        [
          [
            3878
          ],
          [
            3879,
            3880,
            3881
          ]
        ],
        [
          [
            3882
          ],
          [
            3883
          ]
        ],
        [
          [
            3884
          ],
          [
            3885
          ]
        ],
        [
          [
            3886
          ],
          [
            3887,
            3888,
            3889,
            3890,
            3891,
            3892,
            3893,
            3894,
            3895,
            3896,
            3897,
            3898,
            3899,
            3900,
            3901,
            3902,
            3903,
            3904,
            3905,
            3906,
            3907
          ]
        ],
        [
          [
            3908
          ],
          [
            3909
          ]
        ],
        [
          [
            3910
          ],
          [
            3911,
            3912,
            3913
          ]
        ]
      ],
      "ordinal": 100,
      "paragraph_ordinals": [
        3874,
        3875,
        3876,
        3877,
        3878,
        3879,
        3880,
        3881,
        3882,
        3883,
        3884,
        3885,
        3886,
        3887,
        3888,
        3889,
        3890,
        3891,
        3892,
        3893,
        3894,
        3895,
        3896,
        3897,
        3898,
        3899,
        3900,
        3901,
        3902,
        3903,
        3904,
        3905,
        3906,
        3907,
        3908,
        3909,
        3910,
        3911,
        3912,
        3913
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. E2\n2. EVIDENCE\n3. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV08-R0-condition-inventory；\nclaim_level=candidate_description；\nwhen=资源、规则、位置、安全、指标、平台、AI中介或历史沉积可按位置、尺度和时间窗列出，但尚无符合资格的H4-instance。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记候选条件、位置异质性、观察盲区、竞争解释与补证需求。；\nresult_ceiling=仅称条件清单或候选通道；不得把条件人格化，也不得称权力、中介或反身效应已成立。\n2. route_id=HV08-R1-position-or-mediation-effect；\nclaim_level=conditional_effect；\nwhen=H4-instance在证据覆盖、表达安全或对象行为中唯一预选的成功判据取得supported。；\nadditional_inferential_requires=H4-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记该实例位置、中介、结果家族和窗口内的遮蔽、放大或行为响应通道。；\nresult_ceiling=不外推到未选结果家族，不从位置或中介效应推出恶意、责任或自动处置。\n3. route_id=HV08-R2-reflexive-response；\nclaim_level=mechanism_explanation；\nwhen=H4-instance唯一预选反身响应判据，且观测、命名、评分或发布经实际通道到达对象并取得supported。；\nadditional_inferential_requires=H4-instance；\nadditional_protocol_requires=E3、CAUSAL、E4；\nallowed_conclusion=登记指定观测或发布通道与窗口内的反身响应。；\nresult_ceiling=一次响应不称持久反身性；不得据此隐藏观察、压制表达或扩大授权。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 条件性机会、约束、遮蔽与放大"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 条件决定个体行为\n2. 权力位置证明恶意\n3. 环境具有意图"
        ]
      ]
    },
    {
      "anchor": "V82-T101",
      "cell_paragraph_ordinals": [
        [
          [
            3915
          ],
          [
            3916
          ]
        ],
        [
          [
            3917
          ],
          [
            3918
          ]
        ],
        [
          [
            3919
          ],
          [
            3920
          ]
        ],
        [
          [
            3921
          ],
          [
            3922
          ]
        ],
        [
          [
            3923
          ],
          [
            3924,
            3925,
            3926,
            3927
          ]
        ],
        [
          [
            3928
          ],
          [
            3929
          ]
        ],
        [
          [
            3930
          ],
          [
            3931
          ]
        ],
        [
          [
            3932
          ],
          [
            3933
          ]
        ]
      ],
      "ordinal": 101,
      "paragraph_ordinals": [
        3915,
        3916,
        3917,
        3918,
        3919,
        3920,
        3921,
        3922,
        3923,
        3924,
        3925,
        3926,
        3927,
        3928,
        3929,
        3930,
        3931,
        3932,
        3933
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次暴露或评价事件、位置个案、受条件总体、响应分布及聚合规则；X=空间范围：互动现场、组织或平台边界、公开数字空间与跨域环境；T=时间跨度：暴露积累、响应、反身变化与消退窗口；O=组织层级：行动与评价角色、团队、组织、制度至治理生态；C=因果层次：暴露事件、条件—行为互动机制、中观权力结构、制度规则与系统条件；R=观察分辨率：原始暴露表达行为、时间序列、位置个案、响应分布、平台指标与摘要，并登记压缩损失；I=影响范围：直接被评价者、间接受影响者、二阶反身后果、跨域与代际影响；N=网络拓扑范围：权力与信息连接、中介节点、遮蔽区、放大路径与跨域传播；J=管辖与授权范围：规则配置、指标使用、公开评价、人工复核与处置分别登记授权；比较位置异质性"
        ],
        [
          "有效对象（effective_object）",
          "经实际通道改变行动概率、表达安全或证据分布的条件集合"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 条件到行为或证据的机制链"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 位置分布\n2. 条件异质性\n3. 跨域外部性\n4. J轴"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 关键条件与作用强度可随尺度改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无意向行动、权力或制度位置的非人系统"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 局部条件直接普遍化为所有主体的动机"
        ]
      ]
    },
    {
      "anchor": "V82-T102",
      "cell_paragraph_ordinals": [
        [
          [
            3935
          ],
          [
            3936
          ]
        ],
        [
          [
            3937
          ],
          [
            3938,
            3939,
            3940,
            3941,
            3942
          ]
        ],
        [
          [
            3943
          ],
          [
            3944,
            3945,
            3946,
            3947
          ]
        ],
        [
          [
            3948
          ],
          [
            3949,
            3950,
            3951,
            3952
          ]
        ],
        [
          [
            3953
          ],
          [
            3954
          ]
        ],
        [
          [
            3955
          ],
          [
            3956
          ]
        ],
        [
          [
            3957
          ],
          [
            3958
          ]
        ],
        [
          [
            3959
          ],
          [
            3960
          ]
        ],
        [
          [
            3961
          ],
          [
            3962
          ]
        ],
        [
          [
            3963
          ],
          [
            3964,
            3965,
            3966,
            3967
          ]
        ]
      ],
      "ordinal": 102,
      "paragraph_ordinals": [
        3935,
        3936,
        3937,
        3938,
        3939,
        3940,
        3941,
        3942,
        3943,
        3944,
        3945,
        3946,
        3947,
        3948,
        3949,
        3950,
        3951,
        3952,
        3953,
        3954,
        3955,
        3956,
        3957,
        3958,
        3959,
        3960,
        3961,
        3962,
        3963,
        3964,
        3965,
        3966,
        3967
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 支持\n2. 约束\n3. 遮蔽\n4. 放大\n5. 混合"
        ],
        [
          "可观测项（observables）",
          "1. 资源、规则、平台或公开条件改变前后的行为差异\n2. 不同位置的表达安全、证据覆盖和缺席率\n3. 指标、评分或AI中介前后的可见性与处置变化\n4. 比较条件下候选通道效应是否超过预定阈值"
        ],
        [
          "证据要求（evidence）",
          "1. 资源与规则\n2. 位置差异\n3. 平台或指标变化\n4. 行为响应"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 边界与接口2. 观察位置3. 因果合同"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 可行路径2. 表达和证据3. 生成与失稳"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记条件积累、响应与消退时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录不可观察条件、共线性和反身变化"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "因安全、身份或平台门槛而不可见的位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 优势位置\n2. 低权力位置\n3. 中介者\n4. 被评价者"
        ]
      ]
    },
    {
      "anchor": "V82-T103",
      "cell_paragraph_ordinals": [
        [
          [
            3969
          ],
          [
            3970
          ]
        ],
        [
          [
            3971
          ],
          [
            3972,
            3973,
            3974,
            3975,
            3976,
            3977
          ]
        ],
        [
          [
            3978
          ],
          [
            3979,
            3980,
            3981,
            3982
          ]
        ],
        [
          [
            3983
          ],
          [
            3984
          ]
        ],
        [
          [
            3985
          ],
          [
            3986
          ]
        ],
        [
          [
            3987
          ],
          [
            3988
          ]
        ],
        [
          [
            3989
          ],
          [
            3990,
            3991
          ]
        ],
        [
          [
            3992
          ],
          [
            3993
          ]
        ],
        [
          [
            3994
          ],
          [
            3995
          ]
        ]
      ],
      "ordinal": 103,
      "paragraph_ordinals": [
        3969,
        3970,
        3971,
        3972,
        3973,
        3974,
        3975,
        3976,
        3977,
        3978,
        3979,
        3980,
        3981,
        3982,
        3983,
        3984,
        3985,
        3986,
        3987,
        3988,
        3989,
        3990,
        3991,
        3992,
        3993,
        3994,
        3995
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 制度\n2. 资源配置\n3. 平台\n4. 指标\n5. 关系网络\n6. 历史沉积"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 规则制定者\n2. 平台运营者\n3. 资源配置者\n4. 行动决策者"
        ],
        [
          "规范地位（normative_status）",
          "条件优势或筛选结果不构成正当性"
        ],
        [
          "判断上限（judgment_ceiling）",
          "机制链与反事实充分时至解释级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成候选条件通道、位置异质性、证据遮蔽与风险降低需求描述，不授权改变规则平台、资源配置、评价或处置主体；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 相同制度条件下不同安全和权力位置出现相反行动\n2. 以权力或平台标签替代实际因果通道后无法解释状态变化"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，不同位置可经安全可达、反报复通道提交机制差异、缺席信号与安全影响，并触发与原势场判断或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销不成立的势场归因、移除位置标签及其下游评价处置效力并恢复未决状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T104",
      "cell_paragraph_ordinals": [
        [
          [
            3998
          ],
          [
            3999
          ]
        ],
        [
          [
            4000
          ],
          [
            4001
          ]
        ],
        [
          [
            4002
          ],
          [
            4003
          ]
        ],
        [
          [
            4004
          ],
          [
            4005
          ]
        ],
        [
          [
            4006
          ],
          [
            4007
          ]
        ],
        [
          [
            4008
          ],
          [
            4009
          ]
        ],
        [
          [
            4010
          ],
          [
            4011
          ]
        ],
        [
          [
            4012
          ],
          [
            4013
          ]
        ],
        [
          [
            4014
          ],
          [
            4015
          ]
        ]
      ],
      "ordinal": 104,
      "paragraph_ordinals": [
        3998,
        3999,
        4000,
        4001,
        4002,
        4003,
        4004,
        4005,
        4006,
        4007,
        4008,
        4009,
        4010,
        4011,
        4012,
        4013,
        4014,
        4015
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV09"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV09"
        ],
        [
          "名称（name）",
          "结构负荷"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "人类结构负荷必须把任务、协调损耗、维护要求、容量、恢复余量和成本承担位置共同登记。"
        ],
        [
          "适用范围（scope）",
          "持续运转、维护、照护或高压条件下的人类结构"
        ],
        [
          "暂停条件（pause_condition）",
          "只用熵、脆弱或韧性隐喻而无任务、容量和恢复机制"
        ]
      ]
    },
    {
      "anchor": "V82-T105",
      "cell_paragraph_ordinals": [
        [
          [
            4017
          ],
          [
            4018
          ]
        ],
        [
          [
            4019
          ],
          [
            4020
          ]
        ],
        [
          [
            4021
          ],
          [
            4022
          ]
        ],
        [
          [
            4023
          ],
          [
            4024
          ]
        ],
        [
          [
            4025
          ],
          [
            4026
          ]
        ],
        [
          [
            4027
          ],
          [
            4028,
            4029,
            4030,
            4031,
            4032,
            4033,
            4034,
            4035,
            4036,
            4037,
            4038,
            4039,
            4040,
            4041,
            4042,
            4043,
            4044,
            4045,
            4046,
            4047,
            4048
          ]
        ],
        [
          [
            4049
          ],
          [
            4050
          ]
        ],
        [
          [
            4051
          ],
          [
            4052,
            4053,
            4054
          ]
        ]
      ],
      "ordinal": 105,
      "paragraph_ordinals": [
        4017,
        4018,
        4019,
        4020,
        4021,
        4022,
        4023,
        4024,
        4025,
        4026,
        4027,
        4028,
        4029,
        4030,
        4031,
        4032,
        4033,
        4034,
        4035,
        4036,
        4037,
        4038,
        4039,
        4040,
        4041,
        4042,
        4043,
        4044,
        4045,
        4046,
        4047,
        4048,
        4049,
        4050,
        4051,
        4052,
        4053,
        4054
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV09-R0-instant-task-capacity；\nclaim_level=descriptive_classification；\nwhen=同一窗口、位置与类型映射下的任务或协调要求、容量、恢复余量及其分布可观察。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记瞬时任务—容量关系、余量、积压、局部缺口与恢复状态。；\nresult_ceiling=只到同窗描述；瞬时峰值或缺口不自动成为过载机制、累积损伤或崩溃。\n2. route_id=HV09-R1-overload-mechanism；\nclaim_level=mechanism_explanation；\nwhen=CM-LOAD的适用条件完整，且符合资格的G2-instance显示负荷、补给、减载或恢复通道对预选结果有超过阈值效应。；\nadditional_inferential_requires=G2-instance、CM-LOAD；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定位置、类型、窗口和通道内的过载或恢复机制候选。；\nresult_ceiling=不得普遍化为熵、韧性或所有位置必然崩溃，也不直接生成减载或牺牲义务。\n3. route_id=HV09-R2-cumulative-overload；\nclaim_level=intertemporal_explanation；\nwhen=过载机制已有G2-instance与CM-LOAD支持，且G3-instance显示历史负荷对后续容量、错误或恢复具有条件增量。；\nadditional_inferential_requires=G2-instance、CM-LOAD、G3-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记预注册载体、窗口和结果内的累积损伤或迟恢复候选。；\nresult_ceiling=不推出不可逆、必然崩溃、责任归属或具名主体承担义务。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 候选过载、余量不足、维护缺口与恢复差异"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 承接者应继续承担\n2. 高负荷证明奉献\n3. 过载主体等于失稳机制"
        ]
      ]
    },
    {
      "anchor": "V82-T106",
      "cell_paragraph_ordinals": [
        [
          [
            4056
          ],
          [
            4057
          ]
        ],
        [
          [
            4058
          ],
          [
            4059
          ]
        ],
        [
          [
            4060
          ],
          [
            4061
          ]
        ],
        [
          [
            4062
          ],
          [
            4063
          ]
        ],
        [
          [
            4064
          ],
          [
            4065,
            4066,
            4067,
            4068
          ]
        ],
        [
          [
            4069
          ],
          [
            4070
          ]
        ],
        [
          [
            4071
          ],
          [
            4072
          ]
        ],
        [
          [
            4073
          ],
          [
            4074
          ]
        ]
      ],
      "ordinal": 106,
      "paragraph_ordinals": [
        4056,
        4057,
        4058,
        4059,
        4060,
        4061,
        4062,
        4063,
        4064,
        4065,
        4066,
        4067,
        4068,
        4069,
        4070,
        4071,
        4072,
        4073,
        4074
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务负荷、承接个案、岗位或群体总体、负荷容量分布及聚合规则；X=空间范围：工作或照护现场、组织边界、数字劳动空间与跨域外包范围；T=时间跨度：瞬时峰值、持续积压、恢复时滞、跨期与代际窗口；O=组织层级：承接角色、团队、组织、制度至治理生态；C=因果层次：任务事件、任务—容量互动机制、中观瓶颈结构、制度分配与系统条件；R=观察分辨率：原始任务工时记录、负荷序列、承接个案、容量分布、时延错误指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接替代者、二阶外溢、跨域与代际成本；N=网络拓扑范围：任务依赖、关键瓶颈、替代节点、恢复路径与跨域外包网络；J=管辖与授权范围：任务分配、资源调整、停止、绩效使用与补救分别登记授权；保留负荷容量分布"
        ],
        [
          "有效对象（effective_object）",
          "给定窗口内任务和协调要求相对可用容量与恢复余量的结构关系"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 负荷、容量、恢复与成本位置"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 负荷分布\n2. 聚合遮蔽\n3. 责任继承\n4. 代际影响"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 瓶颈、容量和恢复方式可随层级改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无持续非平衡、维护或人类承接要求的过程"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 平均负荷掩盖局部过载"
        ]
      ]
    },
    {
      "anchor": "V82-T107",
      "cell_paragraph_ordinals": [
        [
          [
            4076
          ],
          [
            4077
          ]
        ],
        [
          [
            4078
          ],
          [
            4079,
            4080,
            4081,
            4082,
            4083
          ]
        ],
        [
          [
            4084
          ],
          [
            4085,
            4086,
            4087,
            4088
          ]
        ],
        [
          [
            4089
          ],
          [
            4090,
            4091,
            4092,
            4093,
            4094
          ]
        ],
        [
          [
            4095
          ],
          [
            4096,
            4097,
            4098,
            4099
          ]
        ],
        [
          [
            4100
          ],
          [
            4101
          ]
        ],
        [
          [
            4102
          ],
          [
            4103
          ]
        ],
        [
          [
            4104
          ],
          [
            4105
          ]
        ],
        [
          [
            4106
          ],
          [
            4107
          ]
        ],
        [
          [
            4108
          ],
          [
            4109,
            4110,
            4111,
            4112
          ]
        ]
      ],
      "ordinal": 107,
      "paragraph_ordinals": [
        4076,
        4077,
        4078,
        4079,
        4080,
        4081,
        4082,
        4083,
        4084,
        4085,
        4086,
        4087,
        4088,
        4089,
        4090,
        4091,
        4092,
        4093,
        4094,
        4095,
        4096,
        4097,
        4098,
        4099,
        4100,
        4101,
        4102,
        4103,
        4104,
        4105,
        4106,
        4107,
        4108,
        4109,
        4110,
        4111,
        4112
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 低负荷\n2. 可承受\n3. 临界\n4. 过载\n5. 恢复"
        ],
        [
          "可观测项（observables）",
          "1. 单位时间任务量、积压、时延和错误率\n2. 人员资源容量、隐性劳动与替代可用性\n3. 停止、缺席、退出和恢复曲线\n4. 平均负荷与关键局部承接位置的分布差异"
        ],
        [
          "证据要求（evidence）",
          "1. 任务量\n2. 时延与错误\n3. 人员与资源\n4. 恢复记录\n5. 退出和缺席"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 承接层\n2. 动力—承接链\n3. 条件势场\n4. 瞬时负荷只调用G2与CM-LOAD；累积损伤、迟恢复或历史条件增量另需预注册G3-instance，H5候选留痕不能替代G3"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 状态更新2. 失稳行为3. 维护和修复需求"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "区分即时峰值、持续积压、恢复时滞与代际成本"
        ],
        [
          "不确定性（uncertainty）",
          "记录隐性劳动、外包成本和保护性缺席"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "非正式劳动、家庭照护、外包和低可见承接位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 承接者\n2. 依赖服务者\n3. 替代者\n4. 成本外溢位置"
        ]
      ]
    },
    {
      "anchor": "V82-T108",
      "cell_paragraph_ordinals": [
        [
          [
            4114
          ],
          [
            4115
          ]
        ],
        [
          [
            4116
          ],
          [
            4117,
            4118,
            4119,
            4120,
            4121
          ]
        ],
        [
          [
            4122
          ],
          [
            4123,
            4124,
            4125,
            4126,
            4127
          ]
        ],
        [
          [
            4128
          ],
          [
            4129
          ]
        ],
        [
          [
            4130
          ],
          [
            4131
          ]
        ],
        [
          [
            4132
          ],
          [
            4133
          ]
        ],
        [
          [
            4134
          ],
          [
            4135,
            4136
          ]
        ],
        [
          [
            4137
          ],
          [
            4138
          ]
        ],
        [
          [
            4139
          ],
          [
            4140
          ]
        ]
      ],
      "ordinal": 108,
      "paragraph_ordinals": [
        4114,
        4115,
        4116,
        4117,
        4118,
        4119,
        4120,
        4121,
        4122,
        4123,
        4124,
        4125,
        4126,
        4127,
        4128,
        4129,
        4130,
        4131,
        4132,
        4133,
        4134,
        4135,
        4136,
        4137,
        4138,
        4139,
        4140
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 人员\n2. 岗位\n3. 程序\n4. 设施\n5. 预算"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 任务分配者\n2. 资源配置者\n3. 授权者\n4. 监督者\n5. 补救责任者"
        ],
        [
          "规范地位（normative_status）",
          "高效率或高承载不构成正当性"
        ],
        [
          "判断上限（judgment_ceiling）",
          "负荷容量和恢复证据充分时至诊断级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成负荷、容量、恢复、局部过载与减载补资源需求描述，不授权任务削减、资源投入、绩效处置或强迫承担；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 总体平均容量充足但少数关键承接位置持续过载\n2. 只用熵或韧性隐喻却无法识别任务、容量和恢复通道"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，承接者可经安全可达、反报复通道报告隐性劳动、过载和恢复需求，并触发与原负荷判断、绩效或任务决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误负荷判断及绩效或责任效力，实际恢复任务、资源与记录状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T109",
      "cell_paragraph_ordinals": [
        [
          [
            4143
          ],
          [
            4144
          ]
        ],
        [
          [
            4145
          ],
          [
            4146
          ]
        ],
        [
          [
            4147
          ],
          [
            4148
          ]
        ],
        [
          [
            4149
          ],
          [
            4150
          ]
        ],
        [
          [
            4151
          ],
          [
            4152
          ]
        ],
        [
          [
            4153
          ],
          [
            4154
          ]
        ],
        [
          [
            4155
          ],
          [
            4156
          ]
        ],
        [
          [
            4157
          ],
          [
            4158
          ]
        ],
        [
          [
            4159
          ],
          [
            4160
          ]
        ]
      ],
      "ordinal": 109,
      "paragraph_ordinals": [
        4143,
        4144,
        4145,
        4146,
        4147,
        4148,
        4149,
        4150,
        4151,
        4152,
        4153,
        4154,
        4155,
        4156,
        4157,
        4158,
        4159,
        4160
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV10"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV10"
        ],
        [
          "名称（name）",
          "演化相位"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "S0-S6和X0只适用于存在方向、生成主体或事件、承接层与制度化过程的人类意向性集体，且允许跳阶、并行、混合、回退、分裂、合并、休眠、吞并和功能转移。"
        ],
        [
          "适用范围（scope）",
          "符合适用条件的人类意向性集体"
        ],
        [
          "暂停条件（pause_condition）",
          "适用条件缺失、阶段被道德化或标题与判据不一致"
        ]
      ]
    },
    {
      "anchor": "V82-T110",
      "cell_paragraph_ordinals": [
        [
          [
            4162
          ],
          [
            4163
          ]
        ],
        [
          [
            4164
          ],
          [
            4165,
            4166,
            4167,
            4168
          ]
        ],
        [
          [
            4169
          ],
          [
            4170
          ]
        ],
        [
          [
            4171
          ],
          [
            4172
          ]
        ],
        [
          [
            4173
          ],
          [
            4174
          ]
        ],
        [
          [
            4175
          ],
          [
            4176,
            4177,
            4178,
            4179,
            4180,
            4181,
            4182,
            4183,
            4184,
            4185,
            4186,
            4187,
            4188,
            4189,
            4190,
            4191,
            4192,
            4193,
            4194,
            4195,
            4196,
            4197,
            4198,
            4199,
            4200,
            4201,
            4202,
            4203
          ]
        ],
        [
          [
            4204
          ],
          [
            4205,
            4206,
            4207
          ]
        ],
        [
          [
            4208
          ],
          [
            4209,
            4210,
            4211
          ]
        ]
      ],
      "ordinal": 110,
      "paragraph_ordinals": [
        4162,
        4163,
        4164,
        4165,
        4166,
        4167,
        4168,
        4169,
        4170,
        4171,
        4172,
        4173,
        4174,
        4175,
        4176,
        4177,
        4178,
        4179,
        4180,
        4181,
        4182,
        4183,
        4184,
        4185,
        4186,
        4187,
        4188,
        4189,
        4190,
        4191,
        4192,
        4193,
        4194,
        4195,
        4196,
        4197,
        4198,
        4199,
        4200,
        4201,
        4202,
        4203,
        4204,
        4205,
        4206,
        4207,
        4208,
        4209,
        4210,
        4211
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "1. human_variable:HV03\n2. human_variable:HV04\n3. human_variable:HV05\n4. human_variable:HV07"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. EVIDENCE2. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "无（空集合）"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV10-R0-component-applicability；\nclaim_level=descriptive_classification；\nwhen=HV03、HV04、HV05与HV07已有可审计评估记录；记录允许为missing、not_applicable或unsupported，不要求四组件经验成立。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记适用、不适用、组件缺失、混合状态与继续观察需求。；\nresult_ceiling=组件检查本身不产生S0-S6或X0相位匹配。\n2. route_id=HV10-R1-pattern-phase-match；\nclaim_level=descriptive_classification；\nwhen=CM-PHASE的状态判据、观察窗、混合与转换规则完整，并在重复窗口匹配。；\nadditional_inferential_requires=CM-PHASE；\nadditional_protocol_requires=E4；\nallowed_conclusion=登记S0-S6或X0的原型匹配、混合、并行、回退、休眠或转换描述。；\nresult_ceiling=只到模式相位；相位不是健康、成功、正当性或淘汰等级。\n3. route_id=HV10-R2-causal-transition；\nclaim_level=mechanism_explanation；\nwhen=CM-PHASE匹配成立，且G2-instance识别指定相位转移通道对预选状态变化的效应。；\nadditional_inferential_requires=CM-PHASE、G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定对象、窗口和通道内的候选因果相位转移。；\nresult_ceiling=不得从转移机制推出必然阶段序列、价值方向或推进与淘汰授权。\n4. route_id=HV10-R3-path-dependent-phase；\nclaim_level=intertemporal_explanation；\nwhen=CM-PHASE匹配成立，且G3-instance显示历史相位变量对后续状态、迟滞或回退具有条件增量。；\nadditional_inferential_requires=CM-PHASE、G3-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记预注册窗口内的路径依赖、迟滞或历史相位差异候选。；\nresult_ceiling=不得称命运、绝对不可逆或自动规定修复、退出与退场方案。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 条件性状态坐标\n2. 非线性路径\n3. 有序退场X0"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 所有系统必经S0-S6\n2. 阶段越高越正当\n3. 解体等于失败"
        ]
      ]
    },
    {
      "anchor": "V82-T111",
      "cell_paragraph_ordinals": [
        [
          [
            4213
          ],
          [
            4214
          ]
        ],
        [
          [
            4215
          ],
          [
            4216
          ]
        ],
        [
          [
            4217
          ],
          [
            4218
          ]
        ],
        [
          [
            4219
          ],
          [
            4220,
            4221,
            4222,
            4223
          ]
        ],
        [
          [
            4224
          ],
          [
            4225,
            4226,
            4227,
            4228
          ]
        ],
        [
          [
            4229
          ],
          [
            4230
          ]
        ],
        [
          [
            4231
          ],
          [
            4232
          ]
        ],
        [
          [
            4233
          ],
          [
            4234,
            4235
          ]
        ]
      ],
      "ordinal": 111,
      "paragraph_ordinals": [
        4213,
        4214,
        4215,
        4216,
        4217,
        4218,
        4219,
        4220,
        4221,
        4222,
        4223,
        4224,
        4225,
        4226,
        4227,
        4228,
        4229,
        4230,
        4231,
        4232,
        4233,
        4234,
        4235
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次状态事件、局部群体个案、意向集体总体、相位分布及聚合规则；X=空间范围：行动现场、组织或制度边界、数字协作空间与跨域演化范围；T=时间跨度：状态窗口、转移时滞、回退、休眠、迟滞与代际周期；O=组织层级：成员角色、团队、组织、制度至治理生态；C=因果层次：状态事件、转移互动机制、中观相位结构、制度化过程与系统条件；R=观察分辨率：原始状态事件、转移序列、局部个案、相位分布、状态指标与摘要，并登记压缩损失；I=影响范围：直接成员与承接者、退出者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：局部相位簇群、跨层连接、分裂合并、功能转移与继承路径；J=管辖与授权范围：相位命名、监测采用、试探、推进、退场与淘汰分别登记授权；保留混合相位"
        ],
        [
          "有效对象（effective_object）",
          "具有人类意向、生成、承接和制度化的集体状态"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 适用条件\n2. 相位判据\n3. 非线性路径\n4. X0不计为第八阶段"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 局部相位分布\n2. 跨层转移\n3. 承接继承\n4. 保护与退出"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 承接者、制度载体和有效对象可随相位改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无方向、生成、承接或制度化过程的系统"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 个案相位直接代表总体\n2. 人类阶段迁入通用核心"
        ]
      ]
    },
    {
      "anchor": "V82-T112",
      "cell_paragraph_ordinals": [
        [
          [
            4237
          ],
          [
            4238
          ]
        ],
        [
          [
            4239
          ],
          [
            4240,
            4241,
            4242,
            4243,
            4244,
            4245,
            4246,
            4247
          ]
        ],
        [
          [
            4248
          ],
          [
            4249,
            4250,
            4251,
            4252
          ]
        ],
        [
          [
            4253
          ],
          [
            4254,
            4255,
            4256,
            4257
          ]
        ],
        [
          [
            4258
          ],
          [
            4259,
            4260,
            4261,
            4262,
            4263,
            4264
          ]
        ],
        [
          [
            4265
          ],
          [
            4266
          ]
        ],
        [
          [
            4267
          ],
          [
            4268
          ]
        ],
        [
          [
            4269
          ],
          [
            4270
          ]
        ],
        [
          [
            4271
          ],
          [
            4272
          ]
        ],
        [
          [
            4273
          ],
          [
            4274,
            4275,
            4276,
            4277,
            4278
          ]
        ]
      ],
      "ordinal": 112,
      "paragraph_ordinals": [
        4237,
        4238,
        4239,
        4240,
        4241,
        4242,
        4243,
        4244,
        4245,
        4246,
        4247,
        4248,
        4249,
        4250,
        4251,
        4252,
        4253,
        4254,
        4255,
        4256,
        4257,
        4258,
        4259,
        4260,
        4261,
        4262,
        4263,
        4264,
        4265,
        4266,
        4267,
        4268,
        4269,
        4270,
        4271,
        4272,
        4273,
        4274,
        4275,
        4276,
        4277,
        4278
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. S0\n2. S1\n3. S2\n4. S3\n5. S4\n6. S5\n7. S6\n8. X0转换路径"
        ],
        [
          "可观测项（observables）",
          "1. 方向、生成、承接、制度化和反馈变量的同期状态\n2. 相位判据跨观察窗的重复匹配记录\n3. 跳阶、并行、混合、回退、分裂、合并与休眠轨迹\n4. X0中的功能转移、责任继承与有序退场记录"
        ],
        [
          "证据要求（evidence）",
          "1. 相位变量\n2. 转移记录\n3. 留痕\n4. 承接与制度状态"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 指向锚点\n2. 生成节点\n3. 承接层\n4. 反馈写回\n5. 结构负荷\n6. 模式相位不要求G3；因果转移另需CAUSAL；迟滞、路径依赖或历史效应另需预注册G3-instance，H5只登记候选留痕"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 相位判断2. 承接继承3. 退场和修复需求"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记相位观察窗、转移时滞、回退与休眠"
        ],
        [
          "不确定性（uncertainty）",
          "记录混合相位、分裂、合并与尺度差异"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "总体相位无法代表的局部群体和角色"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 成员\n2. 承接者\n3. 异议者\n4. 退出者\n5. 继承者"
        ]
      ]
    },
    {
      "anchor": "V82-T113",
      "cell_paragraph_ordinals": [
        [
          [
            4280
          ],
          [
            4281
          ]
        ],
        [
          [
            4282
          ],
          [
            4283,
            4284,
            4285,
            4286
          ]
        ],
        [
          [
            4287
          ],
          [
            4288,
            4289
          ]
        ],
        [
          [
            4290
          ],
          [
            4291
          ]
        ],
        [
          [
            4292
          ],
          [
            4293
          ]
        ],
        [
          [
            4294
          ],
          [
            4295
          ]
        ],
        [
          [
            4296
          ],
          [
            4297,
            4298
          ]
        ],
        [
          [
            4299
          ],
          [
            4300
          ]
        ],
        [
          [
            4301
          ],
          [
            4302
          ]
        ]
      ],
      "ordinal": 113,
      "paragraph_ordinals": [
        4280,
        4281,
        4282,
        4283,
        4284,
        4285,
        4286,
        4287,
        4288,
        4289,
        4290,
        4291,
        4292,
        4293,
        4294,
        4295,
        4296,
        4297,
        4298,
        4299,
        4300,
        4301,
        4302
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 集体行动\n2. 组织结构\n3. 制度记录\n4. 共同记忆"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 作出相位判断的分析者\n2. 据此行动的决策与授权者"
        ],
        [
          "规范地位（normative_status）",
          "相位不构成健康、成功或正当性等级"
        ],
        [
          "判断上限（judgment_ceiling）",
          "适用条件和相位证据充分时至原型匹配级"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成相位原型匹配、混合状态、不确定性与观察需求描述，不授权试探、推进、合并、退场或淘汰；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 同一集体同时呈现S2承接成形与S5漏洞积累的混合相位\n2. 有序退场X0保持功能转移而不是阶段失败"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，成员可经安全可达、反报复通道挑战相位证据、线性假设和道德化使用，并触发与原相位判断或决策链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销相位命名及其下游决策效力、实际恢复变量级描述与未决状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T114",
      "cell_paragraph_ordinals": [
        [
          [
            4305
          ],
          [
            4306
          ]
        ],
        [
          [
            4307
          ],
          [
            4308
          ]
        ],
        [
          [
            4309
          ],
          [
            4310
          ]
        ],
        [
          [
            4311
          ],
          [
            4312
          ]
        ],
        [
          [
            4313
          ],
          [
            4314
          ]
        ],
        [
          [
            4315
          ],
          [
            4316
          ]
        ],
        [
          [
            4317
          ],
          [
            4318
          ]
        ],
        [
          [
            4319
          ],
          [
            4320
          ]
        ],
        [
          [
            4321
          ],
          [
            4322
          ]
        ]
      ],
      "ordinal": 114,
      "paragraph_ordinals": [
        4305,
        4306,
        4307,
        4308,
        4309,
        4310,
        4311,
        4312,
        4313,
        4314,
        4315,
        4316,
        4317,
        4318,
        4319,
        4320,
        4321,
        4322
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "接口 ID（id）",
          "HV11"
        ],
        [
          "限定 ID（qualified_id）",
          "human_variable:HV11"
        ],
        [
          "名称（name）",
          "开放性承担行动"
        ],
        [
          "主张类型（claim_type）",
          "H"
        ],
        [
          "合同角色（contract_role）",
          "human_variable_interface"
        ],
        [
          "命题（proposition）",
          "开放性承担只观察真实成本、自愿性、方向、替代解释和结构后果，不诊断某人有没有爱。"
        ],
        [
          "适用范围（scope）",
          "人类关系、组织、制度与公共行动中的承担"
        ],
        [
          "暂停条件（pause_condition）",
          "无法安全确认自愿、拒绝和退出，或分析转向人格与爱的诊断"
        ]
      ]
    },
    {
      "anchor": "V82-T115",
      "cell_paragraph_ordinals": [
        [
          [
            4324
          ],
          [
            4325
          ]
        ],
        [
          [
            4326
          ],
          [
            4327
          ]
        ],
        [
          [
            4328
          ],
          [
            4329,
            4330,
            4331
          ]
        ],
        [
          [
            4332
          ],
          [
            4333
          ]
        ],
        [
          [
            4334
          ],
          [
            4335
          ]
        ],
        [
          [
            4336
          ],
          [
            4337,
            4338,
            4339,
            4340,
            4341,
            4342,
            4343,
            4344,
            4345,
            4346,
            4347,
            4348,
            4349,
            4350,
            4351,
            4352,
            4353,
            4354,
            4355,
            4356,
            4357
          ]
        ],
        [
          [
            4358
          ],
          [
            4359
          ]
        ],
        [
          [
            4360
          ],
          [
            4361,
            4362,
            4363,
            4364
          ]
        ]
      ],
      "ordinal": 115,
      "paragraph_ordinals": [
        4324,
        4325,
        4326,
        4327,
        4328,
        4329,
        4330,
        4331,
        4332,
        4333,
        4334,
        4335,
        4336,
        4337,
        4338,
        4339,
        4340,
        4341,
        4342,
        4343,
        4344,
        4345,
        4346,
        4347,
        4348,
        4349,
        4350,
        4351,
        4352,
        4353,
        4354,
        4355,
        4356,
        4357,
        4358,
        4359,
        4360,
        4361,
        4362,
        4363,
        4364
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "推论依赖（inferential_requires）",
          "无（空集合）"
        ],
        [
          "协议依赖（protocol_requires）",
          "1. N4\n2. EVIDENCE\n3. SOURCE"
        ],
        [
          "限定／特化（specializes）",
          "1. H62. H2"
        ],
        [
          "适用对象引用（applies_to）",
          "无（空集合）"
        ],
        [
          "条件支持路由（conditional_support_routes）",
          "1. route_id=HV11-R0-action-cost-record；\nclaim_level=normative_boundary；\nwhen=行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=描述候选承担行动、成本分布、强制风险、停止权缺口与保护需求。；\nresult_ceiling=不得称开放性承担，不得诊断爱、人格或要求继续承担。\n2. route_id=HV11-R1-voluntary-limited-action；\nclaim_level=normative_boundary；\nwhen=真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；\nadditional_inferential_requires=无（空集合）；\nadditional_protocol_requires=无（空集合）；\nallowed_conclusion=登记有限、自愿且具有方向和可观察后果的开放性承担行动描述。；\nresult_ceiling=只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。\n3. route_id=HV11-R2-structural-consequence；\nclaim_level=conditional_effect；\nwhen=符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；\nadditional_inferential_requires=G2-instance；\nadditional_protocol_requires=CAUSAL、E4；\nallowed_conclusion=登记指定通道、对象与窗口内的行动结构后果。；\nresult_ceiling=结构效应不证明爱、善、正当性、无限责任或行动授权。"
        ],
        [
          "允许推论（allowed_inference）",
          "1. 描述有限承担行动与后果"
        ],
        [
          "禁止跳跃（prohibited_leap）",
          "1. 诊断有没有爱\n2. 牺牲等于爱\n3. 责任等于无限承担\n4. 拒绝等于道德失败"
        ]
      ]
    },
    {
      "anchor": "V82-T116",
      "cell_paragraph_ordinals": [
        [
          [
            4366
          ],
          [
            4367
          ]
        ],
        [
          [
            4368
          ],
          [
            4369
          ]
        ],
        [
          [
            4370
          ],
          [
            4371
          ]
        ],
        [
          [
            4372
          ],
          [
            4373
          ]
        ],
        [
          [
            4374
          ],
          [
            4375,
            4376,
            4377,
            4378
          ]
        ],
        [
          [
            4379
          ],
          [
            4380
          ]
        ],
        [
          [
            4381
          ],
          [
            4382
          ]
        ],
        [
          [
            4383
          ],
          [
            4384,
            4385
          ]
        ]
      ],
      "ordinal": 116,
      "paragraph_ordinals": [
        4366,
        4367,
        4368,
        4369,
        4370,
        4371,
        4372,
        4373,
        4374,
        4375,
        4376,
        4377,
        4378,
        4379,
        4380,
        4381,
        4382,
        4383,
        4384,
        4385
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "九轴尺度画像（scale_profile）",
          "SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次承担行动、行动者个案、关系或组织总体、成本自愿性分布及聚合规则；X=空间范围：关系与照护现场、组织边界、数字公共空间与跨域受益范围；T=时间跨度：即时行动、持续承担、耗竭、恢复与代际窗口；O=组织层级：行动角色、关系或团队、组织、制度至治理生态；C=因果层次：承担事件、行动—成本互动机制、中观关系结构、制度责任安排与系统条件；R=观察分辨率：原始行动与成本、承担序列、行动者个案、成本自愿性分布、后果指标与摘要，并登记压缩损失；I=影响范围：直接行动者与受益者、依赖者、间接替代承接者、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖照护、受益连接、替代承接、退出路径与跨域成本网络；J=管辖与授权范围：承担要求、资源使用、拒绝、停止、保护与补救分别登记授权；保留自愿成本退出差异"
        ],
        [
          "有效对象（effective_object）",
          "满足真实成本、自愿性、方向和结构后果条件的人类行动"
        ],
        [
          "跨尺度保持项（scale_invariants）",
          "1. 成本、自愿性、方向、替代解释、后果与停止权"
        ],
        [
          "升格必补项（required_scale_additions）",
          "1. 自愿性分布\n2. 代表关系\n3. 成本外溢\n4. 真实退出与代理保护"
        ],
        [
          "随尺度改变项（changing_semantics）",
          "1. 承担形式、成本位置和受益对象可改变"
        ],
        [
          "不适用对象（non_applicable_objects）",
          "1. 无意向、自愿性、责任或意义能力的非人系统"
        ],
        [
          "禁止升格（forbidden_elevation）",
          "1. 个体承担升格为群体义务\n2. 人类承担概念迁入非人核心"
        ]
      ]
    },
    {
      "anchor": "V82-T117",
      "cell_paragraph_ordinals": [
        [
          [
            4387
          ],
          [
            4388
          ]
        ],
        [
          [
            4389
          ],
          [
            4390,
            4391,
            4392,
            4393,
            4394
          ]
        ],
        [
          [
            4395
          ],
          [
            4396,
            4397,
            4398,
            4399
          ]
        ],
        [
          [
            4400
          ],
          [
            4401,
            4402,
            4403,
            4404
          ]
        ],
        [
          [
            4405
          ],
          [
            4406,
            4407,
            4408,
            4409
          ]
        ],
        [
          [
            4410
          ],
          [
            4411,
            4412,
            4413
          ]
        ],
        [
          [
            4414
          ],
          [
            4415
          ]
        ],
        [
          [
            4416
          ],
          [
            4417
          ]
        ],
        [
          [
            4418
          ],
          [
            4419
          ]
        ],
        [
          [
            4420
          ],
          [
            4421,
            4422,
            4423,
            4424
          ]
        ]
      ],
      "ordinal": 117,
      "paragraph_ordinals": [
        4387,
        4388,
        4389,
        4390,
        4391,
        4392,
        4393,
        4394,
        4395,
        4396,
        4397,
        4398,
        4399,
        4400,
        4401,
        4402,
        4403,
        4404,
        4405,
        4406,
        4407,
        4408,
        4409,
        4410,
        4411,
        4412,
        4413,
        4414,
        4415,
        4416,
        4417,
        4418,
        4419,
        4420,
        4421,
        4422,
        4423,
        4424
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "状态集合（state）",
          "1. 候选\n2. 自愿且有限\n3. 强制风险\n4. 单方耗竭\n5. 停止或退出"
        ],
        [
          "可观测项（observables）",
          "1. 行动投入的时间、资源、机会与身体心理成本\n2. 拒绝、退出、停止和重新协商是否真实可用\n3. 行动方向、受益位置和可检测结构后果\n4. 强制、恐惧、依赖、利益与表演等替代解释"
        ],
        [
          "证据要求（evidence）",
          "1. 行动与成本\n2. 拒绝和退出条件\n3. 替代解释\n4. 受益与后果"
        ],
        [
          "输入依赖与接口内容（input_dependencies）",
          "1. 指向锚点\n2. 承接层\n3. 条件势场\n4. 权力与安全"
        ],
        [
          "输出效应与变量流（output_effects）",
          "1. 成本分布\n2. 关系和制度状态\n3. 停止与修复"
        ],
        [
          "时间窗与时滞（time_window_and_lag）",
          "登记即时成本、持续承担、耗竭与恢复时滞"
        ],
        [
          "不确定性（uncertainty）",
          "记录依赖、恐惧、隐性强制与表达安全"
        ],
        [
          "局部排除区（local_exclusion_zone）",
          "无法安全拒绝、无法退出或被道德压力遮蔽的位置"
        ],
        [
          "受影响位置（affected_positions）",
          "1. 行动者\n2. 受益者\n3. 依赖者\n4. 替代承接者"
        ]
      ]
    },
    {
      "anchor": "V82-T118",
      "cell_paragraph_ordinals": [
        [
          [
            4426
          ],
          [
            4427
          ]
        ],
        [
          [
            4428
          ],
          [
            4429,
            4430,
            4431
          ]
        ],
        [
          [
            4432
          ],
          [
            4433,
            4434,
            4435,
            4436
          ]
        ],
        [
          [
            4437
          ],
          [
            4438
          ]
        ],
        [
          [
            4439
          ],
          [
            4440
          ]
        ],
        [
          [
            4441
          ],
          [
            4442
          ]
        ],
        [
          [
            4443
          ],
          [
            4444,
            4445
          ]
        ],
        [
          [
            4446
          ],
          [
            4447
          ]
        ],
        [
          [
            4448
          ],
          [
            4449
          ]
        ]
      ],
      "ordinal": 118,
      "paragraph_ordinals": [
        4426,
        4427,
        4428,
        4429,
        4430,
        4431,
        4432,
        4433,
        4434,
        4435,
        4436,
        4437,
        4438,
        4439,
        4440,
        4441,
        4442,
        4443,
        4444,
        4445,
        4446,
        4447,
        4448,
        4449
      ],
      "rows": [
        [
          "字段",
          "登记内容"
        ],
        [
          "承接载体（carrier）",
          "1. 具体行动者\n2. 关系实践\n3. 照护或责任安排"
        ],
        [
          "责任主体（responsible_subject）",
          "1. 提出要求者\n2. 授权者\n3. 受益责任者\n4. 补救责任者"
        ],
        [
          "规范地位（normative_status）",
          "受N4约束，不可命令或征用"
        ],
        [
          "判断上限（judgment_ceiling）",
          "证据充分时只到行动描述级，不进入人格诊断"
        ],
        [
          "行动上限（action_ceiling）",
          "本变量只生成自愿性、真实成本、方向、替代解释、结构后果与停止保护需求描述，不授权保护措施、承担要求、资源征用或人格裁决；任何现实调整须另过C12、运行时显式N前提、J授权与O程序"
        ],
        [
          "反例（counterexamples）",
          "1. 无法拒绝的单方牺牲被赞美为爱或责任\n2. 承担宣称没有真实成本、行动方向或可检测结构后果"
        ],
        [
          "申诉（appeal）",
          "依appeal_and_rollback_rule，行动者可经安全可达、反报复通道拒绝被代表，说明强制、成本、替代解释和退出限制，并触发与原承担判断或要求链独立的复核"
        ],
        [
          "回滚（rollback）",
          "依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销承担命名与相关要求，实际恢复拒绝、退出、记录和资源状态，保留版本与完成验证"
        ]
      ]
    },
    {
      "anchor": "V82-T119",
      "cell_paragraph_ordinals": [
        [
          [
            4453
          ],
          [
            4454
          ]
        ],
        [
          [
            4455
          ],
          [
            4456
          ]
        ],
        [
          [
            4457
          ],
          [
            4458
          ]
        ],
        [
          [
            4459
          ],
          [
            4460
          ]
        ],
        [
          [
            4461
          ],
          [
            4462
          ]
        ],
        [
          [
            4463
          ],
          [
            4464
          ]
        ],
        [
          [
            4465
          ],
          [
            4466
          ]
        ],
        [
          [
            4467
          ],
          [
            4468
          ]
        ],
        [
          [
            4469
          ],
          [
            4470
          ]
        ],
        [
          [
            4471
          ],
          [
            4472
          ]
        ],
        [
          [
            4473
          ],
          [
            4474
          ]
        ],
        [
          [
            4475
          ],
          [
            4476
          ]
        ]
      ],
      "ordinal": 119,
      "paragraph_ordinals": [
        4453,
        4454,
        4455,
        4456,
        4457,
        4458,
        4459,
        4460,
        4461,
        4462,
        4463,
        4464,
        4465,
        4466,
        4467,
        4468,
        4469,
        4470,
        4471,
        4472,
        4473,
        4474,
        4475,
        4476
      ],
      "rows": [
        [
          "变量",
          "本变量可生成的描述或需求"
        ],
        [
          "HV01",
          "候选结构域、边界争议与补证需求"
        ],
        [
          "HV02",
          "边界状态、接口障碍、排除风险与测试需求"
        ],
        [
          "HV03",
          "候选锚点、异质表达、比较结果与补证需求"
        ],
        [
          "HV04",
          "GC、GS、GE 候选分型、状态转移与补证需求"
        ],
        [
          "HV05",
          "CV、RS、成本、容量、停止权、承接缺口及减载、补资源或重分配需求"
        ],
        [
          "HV06",
          "链条连通、时滞、损耗、中断、成本与承接需求"
        ],
        [
          "HV07",
          "受理、字段变化、执行、持续时间、写回缺口与程序修复需求"
        ],
        [
          "HV08",
          "候选条件通道、位置异质性、证据遮蔽与风险降低需求"
        ],
        [
          "HV09",
          "负荷、容量、恢复、局部过载与减载补资源需求"
        ],
        [
          "HV10",
          "相位原型匹配、混合状态、不确定性与观察需求"
        ],
        [
          "HV11",
          "自愿性、真实成本、方向、替代解释、结构后果与停止保护需求"
        ]
      ]
    }
  ]
}
```
<!-- canonical-records:end -->
