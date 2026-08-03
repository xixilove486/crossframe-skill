# CrossFrame Ultra v8.2 第十一部分　事件驱动的动态推演

Raw SHA256: `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
Source role: `division`
Paragraph range: `V82-P1931`-`V82-P2131`
Paragraph count: `201`
Tables: `V82-T042, V82-T043, V82-T044, V82-T045, V82-T046, V82-T047`

## Source Paragraphs

<!-- source-paragraph:V82-P1931 style=PartTitle -->
第十一部分　事件驱动的动态推演

<!-- source-paragraph:V82-P1932 style=BodyCJK -->
动态推演回答的不是“世界接下来一定会怎样”，而是：从一个冻结的联合状态出发，在某个观察事件、情景事件或已授权行动发生后，哪些变量会先改变，影响沿什么通道传播，何处出现时延、阈值、反馈、跨圈层级联与分叉，哪些信号会提高或降低某条路径的支持度。

<!-- source-paragraph:V82-P1933 style=SecH2 -->
11.1　推演与叙事续写的区别

<!-- source-paragraph:V82-P1934 style=BodyCJK -->
叙事续写可以凭连贯性选择一个后续；结构推演必须保留条件、通道、竞争路径和失败语义。若缺少关键变量，推演应停在未知或生成变量候选，而不是用最顺畅的故事补齐。若多个后续都与现有证据一致，就保持分叉；若路径无法比较，就不强制排序。

<!-- source-paragraph:V82-P1935 style=BodyCJK -->
推演的最小输入为冻结快照、事件记录、机制假设、参数范围、时钟政策、传播政策、未知项和停止条件。最小输出为路径图、每一步状态差、支持状态、早期信号、反向信号、残差、变量候选和回写要求。

<!-- source-paragraph:V82-P1936 style=TableHead -->
输入

<!-- source-paragraph:V82-P1937 style=TableHead -->
必须冻结的内容

<!-- source-paragraph:V82-P1938 style=TableHead -->
不冻结的后果

<!-- source-paragraph:V82-P1939 style=TableText -->
联合快照

<!-- source-paragraph:V82-P1940 style=TableText -->
行动者、圈层、关系、M/Ψ、时钟、证据截止

<!-- source-paragraph:V82-P1941 style=TableText -->
结果后改写起点

<!-- source-paragraph:V82-P1942 style=TableText -->
事件

<!-- source-paragraph:V82-P1943 style=TableText -->
类型、时间、来源、触达对象与通道

<!-- source-paragraph:V82-P1944 style=TableText -->
把传闻、计划和事实混装

<!-- source-paragraph:V82-P1945 style=TableText -->
机制

<!-- source-paragraph:V82-P1946 style=TableText -->
方向、载体、时延、阈值、失效条件

<!-- source-paragraph:V82-P1947 style=TableText -->
任意解释每个结果

<!-- source-paragraph:V82-P1948 style=TableText -->
参数

<!-- source-paragraph:V82-P1949 style=TableText -->
值、区间、等级或明确未知

<!-- source-paragraph:V82-P1950 style=TableText -->
用伪精确掩盖不确定

<!-- source-paragraph:V82-P1951 style=TableText -->
停止

<!-- source-paragraph:V82-P1952 style=TableText -->
信息、风险、越界与资源条件

<!-- source-paragraph:V82-P1953 style=TableText -->
无限制向后讲故事

<!-- source-paragraph:V82-P1954 style=SecH2 -->
11.2　事件合同

<!-- source-paragraph:V82-P1955 style=BodyCJK -->
事件包括观察到、被报告、计划中、假设性和模拟五类。类型必须进入记录：被报告的事件可以影响相信它的人，但不能自动当作已发生；计划可能改变预期，却不等于执行；假设事件用于条件分析；模拟事件只属于模型运行，不能回写现实事实。

<!-- source-paragraph:V82-P1956 style=BodyCJK -->
事件记录至少包含：事件 ID、发生时间或窗口、观察时间、来源、受影响行动者、受影响圈层、通道、直接变化、证据状态、争议、竞争解释、可逆性、持续时间和后续观测。

<!-- source-paragraph:V82-P1957 style=TableHead -->
事件类型

<!-- source-paragraph:V82-P1958 style=TableHead -->
可以进入哪种推演

<!-- source-paragraph:V82-P1959 style=TableHead -->
事实地位

<!-- source-paragraph:V82-P1960 style=TableHead -->
必须附加的限制

<!-- source-paragraph:V82-P1961 style=TableText -->
观察到

<!-- source-paragraph:V82-P1962 style=TableText -->
解释、回放、前向推演

<!-- source-paragraph:V82-P1963 style=TableText -->
在观察合同内成立

<!-- source-paragraph:V82-P1964 style=TableText -->
来源、遗漏和测量误差

<!-- source-paragraph:V82-P1965 style=TableText -->
被报告

<!-- source-paragraph:V82-P1966 style=TableText -->
信念传播和条件推演

<!-- source-paragraph:V82-P1967 style=TableText -->
报告发生，不等于内容为真

<!-- source-paragraph:V82-P1968 style=TableText -->
报告者位置、核验和争议

<!-- source-paragraph:V82-P1969 style=TableText -->
计划中

<!-- source-paragraph:V82-P1970 style=TableText -->
预期、准备与策略互动

<!-- source-paragraph:V82-P1971 style=TableText -->
计划存在，不等于执行

<!-- source-paragraph:V82-P1972 style=TableText -->
授权、资源和取消条件

<!-- source-paragraph:V82-P1973 style=TableText -->
假设性

<!-- source-paragraph:V82-P1974 style=TableText -->
反事实与情景比较

<!-- source-paragraph:V82-P1975 style=TableText -->
非现实事实

<!-- source-paragraph:V82-P1976 style=TableText -->
条件、目的和可实现性

<!-- source-paragraph:V82-P1977 style=TableText -->
模拟

<!-- source-paragraph:V82-P1978 style=TableText -->
模型内部路径展开

<!-- source-paragraph:V82-P1979 style=TableText -->
仅模型状态

<!-- source-paragraph:V82-P1980 style=TableText -->
模型版本、参数和禁止外推

<!-- source-paragraph:V82-P1981 style=SecH2 -->
11.3　联合状态更新式

<!-- source-paragraph:V82-P1982 style=BodyCJK -->
联合状态可写为：

<!-- source-paragraph:V82-P1983 style=BodyCJK -->
Ω(t) = <A(t), C(t), R(t), M(t), Ψ(t), Q(t), E≤t, SP(t), W(t), K(t)>。

<!-- source-paragraph:V82-P1984 style=BodyCJK -->
一次更新可写为：

<!-- source-paragraph:V82-P1985 style=BodyCJK -->
Ω(t+Δ) = F[Ω(t), e(t), u(t), ξ(t) | θ, h]。

<!-- source-paragraph:V82-P1986 style=BodyCJK -->
e(t) 是事件，u(t) 是已获外部授权且实际发生的行动，ξ(t) 是外生扰动或未建模残差，θ 是冻结的机制与参数假设，h 是历史项。这个式子只规定记录责任，不宣称存在唯一真实的 F，也不允许用函数符号替代具体机制。

<!-- source-paragraph:V82-P1987 style=BodyCJK -->
每次更新都要区分：直接观察的状态差；由机制合同支持的推断；为探索路径设定的情景值；尚未解释的残差。四者在后续路径中保持来源，不因共同出现在一个快照中而获得相同证据地位。

<!-- source-paragraph:V82-P1988 style=SecH2 -->
11.4　九步推演闭环

<!-- source-paragraph:V82-P1989 style=SecH3 -->
11.4.1　第一步：冻结当前状态

<!-- source-paragraph:V82-P1990 style=BodyCJK -->
记录证据截止、对象、变量、未知、争议和模型版本。截止后获得的信息不能倒灌到起点；若需使用，建立新运行版本。

<!-- source-paragraph:V82-P1991 style=SecH3 -->
11.4.2　第二步：识别行动者与圈层

<!-- source-paragraph:V82-P1992 style=BodyCJK -->
调用第九、十部分。圈层不足以获得对象支持时保留候选分组；人格不足以获得支持时保留变量候选。不能为了使图完整而强行实体化。

<!-- source-paragraph:V82-P1993 style=SecH3 -->
11.4.3　第三步：分离双通道条件

<!-- source-paragraph:V82-P1994 style=BodyCJK -->
把物质条件和体验—意义条件分别列出，并声明可能的跨通道桥。若只有一种条件有证据，另一种保持未知，不用对称假设补齐。

<!-- source-paragraph:V82-P1995 style=SecH3 -->
11.4.4　第四步：声明时钟、阈值、容量与时延

<!-- source-paragraph:V82-P1996 style=BodyCJK -->
每个变量标明更新时钟。通道若有容量、延迟、损耗、饱和、反转或恢复窗口，应在传播前登记。

<!-- source-paragraph:V82-P1997 style=SecH3 -->
11.4.5　第五步：注入事件或行动

<!-- source-paragraph:V82-P1998 style=BodyCJK -->
一次运行可以包含多个按时间排序的事件，但每个事件必须保留独立记录。行动必须有外部授权引用；没有授权时只能作为假设情景，而不能写成待执行指令。

<!-- source-paragraph:V82-P1999 style=SecH3 -->
11.4.6　第六步：沿已声明通道传播

<!-- source-paragraph:V82-P2000 style=BodyCJK -->
先记录直接效应，再记录返回信号、间接效应和跨圈层级联。没有通道的影响保持候选，不因相关同时出现而连接。

<!-- source-paragraph:V82-P2001 style=SecH3 -->
11.4.7　第七步：在分叉点生成路径

<!-- source-paragraph:V82-P2002 style=BodyCJK -->
条件、阈值、行动者选择、外部扰动或机制不确定都可能产生分叉。互斥路径分开；可以同时发生的路径保留并行；只有合并条件明确时才建立汇合节点。

<!-- source-paragraph:V82-P2003 style=SecH3 -->
11.4.8　第八步：登记信号、残差与变量候选

<!-- source-paragraph:V82-P2004 style=BodyCJK -->
每条路径列出早期信号和反向信号。无法由当前变量解释的状态差进入残差；残差可以触发变量候选账本，但不能自动生成现实取值。

<!-- source-paragraph:V82-P2005 style=SecH3 -->
11.4.9　第九步：结果回写

<!-- source-paragraph:V82-P2006 style=BodyCJK -->
真实结果到来后追加记录：哪条路径得到支持，哪些时点偏离，简单基线是否更好，校准如何，哪些机制或变量应降级、分裂、修改边界或退役。回写不覆盖原运行。

<!-- source-paragraph:V82-P2007 style=SecH2 -->
11.5　传播、时延与阈值

<!-- source-paragraph:V82-P2008 style=BodyCJK -->
传播至少区分信号到达和有效状态改变。信息被看到但没有改变后续转移，只登记到达；改变了信念但没有行动，登记体验—意义状态变化；改变了资源、行为、规则或关系，才登记相应结构变化。

<!-- source-paragraph:V82-P2009 style=TableHead -->
传播要素

<!-- source-paragraph:V82-P2010 style=TableHead -->
记录问题

<!-- source-paragraph:V82-P2011 style=TableHead -->
可能的非线性

<!-- source-paragraph:V82-P2012 style=TableText -->
通道

<!-- source-paragraph:V82-P2013 style=TableText -->
什么载体把影响从源带到目标

<!-- source-paragraph:V82-P2014 style=TableText -->
通道关闭、过滤或替代

<!-- source-paragraph:V82-P2015 style=TableText -->
容量

<!-- source-paragraph:V82-P2016 style=TableText -->
单位时间可承载多少

<!-- source-paragraph:V82-P2017 style=TableText -->
饱和、拥堵、排队

<!-- source-paragraph:V82-P2018 style=TableText -->
时延

<!-- source-paragraph:V82-P2019 style=TableText -->
何时到达、何时产生效果

<!-- source-paragraph:V82-P2020 style=TableText -->
延迟反馈、误判无效

<!-- source-paragraph:V82-P2021 style=TableText -->
阈值

<!-- source-paragraph:V82-P2022 style=TableText -->
达到什么条件才改变状态

<!-- source-paragraph:V82-P2023 style=TableText -->
突变、迟滞、级联

<!-- source-paragraph:V82-P2024 style=TableText -->
损耗

<!-- source-paragraph:V82-P2025 style=TableText -->
传播中丢失或转化什么

<!-- source-paragraph:V82-P2026 style=TableText -->
意义漂移、资源耗散

<!-- source-paragraph:V82-P2027 style=TableText -->
方向

<!-- source-paragraph:V82-P2028 style=TableText -->
影响是否对称

<!-- source-paragraph:V82-P2029 style=TableText -->
单向依赖、反向抵消

<!-- source-paragraph:V82-P2030 style=TableText -->
恢复

<!-- source-paragraph:V82-P2031 style=TableText -->
冲击后如何回到或转到新状态

<!-- source-paragraph:V82-P2032 style=TableText -->
弹性、累积损伤、锁定

<!-- source-paragraph:V82-P2033 style=BodyCJK -->
同一事件经不同通道到达不同圈层时，效果可以相反。资源增加可能降低一个圈层的负荷，却提高另一个圈层的竞争；公开说明可能修复外部合法性，却激活内部羞耻或不信任。推演应逐通道记录，不能用净效应掩盖分配差异。

<!-- source-paragraph:V82-P2034 style=SecH2 -->
11.6　反馈与跨圈层级联

<!-- source-paragraph:V82-P2035 style=BodyCJK -->
反馈要求先前状态或输出经返回通道改变后续状态、转移概率或约束。级联要求一个局部变化经成员重叠、桥接、共享资源、制度下行或网络传播触发其他圈层变化。两者都要有时间顺序和通道证据。

<!-- source-paragraph:V82-P2036 style=TableHead -->
级联类型

<!-- source-paragraph:V82-P2037 style=TableHead -->
典型链条

<!-- source-paragraph:V82-P2038 style=TableHead -->
观察重点

<!-- source-paragraph:V82-P2039 style=TableHead -->
停止条件

<!-- source-paragraph:V82-P2040 style=TableText -->
成员级联

<!-- source-paragraph:V82-P2041 style=TableText -->
重叠成员把行为、情绪或信息带入另一圈层

<!-- source-paragraph:V82-P2042 style=TableText -->
真实传导而非共同背景

<!-- source-paragraph:V82-P2043 style=TableText -->
成员不再参与或信息未被接收

<!-- source-paragraph:V82-P2044 style=TableText -->
资源级联

<!-- source-paragraph:V82-P2045 style=TableText -->
一个圈层占用、释放或重配资源

<!-- source-paragraph:V82-P2046 style=TableText -->
会计边界、转换和损耗

<!-- source-paragraph:V82-P2047 style=TableText -->
资源隔离或替代来源

<!-- source-paragraph:V82-P2048 style=TableText -->
意义级联

<!-- source-paragraph:V82-P2049 style=TableText -->
事件解释改变身份、合法性或信任

<!-- source-paragraph:V82-P2050 style=TableText -->
不同位置的解释差异

<!-- source-paragraph:V82-P2051 style=TableText -->
意义未改变行动或规则

<!-- source-paragraph:V82-P2052 style=TableText -->
制度级联

<!-- source-paragraph:V82-P2053 style=TableText -->
申诉、审计或事件改变规则并下行执行

<!-- source-paragraph:V82-P2054 style=TableText -->
决定、执行和实际写回

<!-- source-paragraph:V82-P2055 style=TableText -->
规则未落实或被局部抵消

<!-- source-paragraph:V82-P2056 style=TableText -->
平台级联

<!-- source-paragraph:V82-P2057 style=TableText -->
推荐、指标或公开评价放大传播

<!-- source-paragraph:V82-P2058 style=TableText -->
算法、选择性可见和反身性

<!-- source-paragraph:V82-P2059 style=TableText -->
曝光不再增长或受众不响应

<!-- source-paragraph:V82-P2060 style=BodyCJK -->
级联不是规模越大越重要。小圈层可能通过关键桥接产生高影响，大圈层可能因通道阻断而没有有效传播。推演应关注位置、通道和阈值，而不是只看成员数量。

<!-- source-paragraph:V82-P2061 style=SecH2 -->
11.7　分叉路径图

<!-- source-paragraph:V82-P2062 style=BodyCJK -->
路径节点至少包含父节点、条件集、触发事件或行动、状态差、受影响时钟、支持状态、概率或排序表达、早期信号、反向信号、下一节点和终止理由。路径图应是有向无环图；若现实出现循环反馈，用时间展开后的新节点表示，不能让一个节点在同一次运行中既是自己的原因又是结果。

<!-- source-paragraph:V82-P2063 style=BodyCJK -->
分叉可由四类不确定产生：事实不确定、机制不确定、行动者选择和外生扰动。不同类型不应合并成一个模糊概率。事实不确定优先核验；机制不确定通过区分性观察；选择不确定保留策略与授权；外生扰动通过情景范围和韧性检查。

<!-- source-paragraph:V82-P2064 style=TableHead -->
分叉来源

<!-- source-paragraph:V82-P2065 style=TableHead -->
例子

<!-- source-paragraph:V82-P2066 style=TableHead -->
合适输出

<!-- source-paragraph:V82-P2067 style=TableHead -->
不合适输出

<!-- source-paragraph:V82-P2068 style=TableText -->
事实

<!-- source-paragraph:V82-P2069 style=TableText -->
事件是否真实发生

<!-- source-paragraph:V82-P2070 style=TableText -->
核验前的条件路径

<!-- source-paragraph:V82-P2071 style=TableText -->
选一个版本当事实

<!-- source-paragraph:V82-P2072 style=TableText -->
机制

<!-- source-paragraph:V82-P2073 style=TableText -->
沉默来自恐惧还是策略

<!-- source-paragraph:V82-P2074 style=TableText -->
区分信号和并行路径

<!-- source-paragraph:V82-P2075 style=TableText -->
用人格标签封口

<!-- source-paragraph:V82-P2076 style=TableText -->
选择

<!-- source-paragraph:V82-P2077 style=TableText -->
行动者合作、抵抗或退出

<!-- source-paragraph:V82-P2078 style=TableText -->
各选择的条件与后果

<!-- source-paragraph:V82-P2079 style=TableText -->
宣称自由选择可精确预测

<!-- source-paragraph:V82-P2080 style=TableText -->
扰动

<!-- source-paragraph:V82-P2081 style=TableText -->
政策、价格、灾害或技术变化

<!-- source-paragraph:V82-P2082 style=TableText -->
压力情景与恢复条件

<!-- source-paragraph:V82-P2083 style=TableText -->
把未建模残差归因于命运

<!-- source-paragraph:V82-P2084 style=SecH2 -->
11.8　变量候选账本

<!-- source-paragraph:V82-P2085 style=BodyCJK -->
模型无法解释的残差不能被删除，也不能立即命名成真实变量。候选账本把“我们可能漏了什么”转成可检验任务。每个候选至少记录来源残差、名称、可能类型、可能通道、可观察含义、竞争候选、最小检验、隐私与风险、当前状态、证据、升级和拒绝条件。

<!-- source-paragraph:V82-P2086 style=BodyCJK -->
候选状态包括提出、检验中、得到支持的候选、拒绝和退役。即使得到支持，它仍要进入相应对象或变量合同，不能直接变成稳定人格、有效圈层或因果机制。结果后提出的候选可以改善下一轮模型，不能回头支撑原预测。

<!-- source-paragraph:V82-P2087 style=TableHead -->
候选来源

<!-- source-paragraph:V82-P2088 style=TableHead -->
合法动作

<!-- source-paragraph:V82-P2089 style=TableHead -->
必须避免

<!-- source-paragraph:V82-P2090 style=TableText -->
系统残差

<!-- source-paragraph:V82-P2091 style=TableText -->
提出多个竞争候选和区分性观察

<!-- source-paragraph:V82-P2092 style=TableText -->
用一个神秘变量吸收全部误差

<!-- source-paragraph:V82-P2093 style=TableText -->
当事人叙述

<!-- source-paragraph:V82-P2094 style=TableText -->
保留其位置、含义和可核验部分

<!-- source-paragraph:V82-P2095 style=TableText -->
自动降格为主观噪声或升格为事实全貌

<!-- source-paragraph:V82-P2096 style=TableText -->
跨案例重复

<!-- source-paragraph:V82-P2097 style=TableText -->
建立候选机制与外推边界

<!-- source-paragraph:V82-P2098 style=TableText -->
把相似叙事当通用规律

<!-- source-paragraph:V82-P2099 style=TableText -->
模型搜索

<!-- source-paragraph:V82-P2100 style=TableText -->
预注册下一轮检验

<!-- source-paragraph:V82-P2101 style=TableText -->
结果后择优报告

<!-- source-paragraph:V82-P2102 style=TableText -->
AI 建议

<!-- source-paragraph:V82-P2103 style=TableText -->
仅作为候选生成

<!-- source-paragraph:V82-P2104 style=TableText -->
让 AI 输出验证现实或授权行动

<!-- source-paragraph:V82-P2105 style=BodyCJK -->
框架只能主动识别当前变量集无法解释的残差，提出多个可区分的变量候选，并为每个候选设计风险可接受的最小检验；它不能自主决定候选在现实中为真。

<!-- source-paragraph:V82-P2106 style=SecH2 -->
11.9　情景、反事实与模拟

<!-- source-paragraph:V82-P2107 style=BodyCJK -->
情景推演问“如果这些条件成立，会出现什么路径”；反事实问“若某个事件或机制不同，已发生结果可能如何变化”；模拟把明确规则和参数展开。三者都需要与事实描述分开。

<!-- source-paragraph:V82-P2108 style=BodyCJK -->
反事实尤其需要可比条件。删除一个事件时，还要说明哪些后续状态、行动者信息和圈层关系随之改变；不能只删除不喜欢的原因而保留其全部后果。模拟的精度不能超过输入和机制证据，参数未知时使用区间、等级或敏感性分析，不生成没有依据的小数点。

<!-- source-paragraph:V82-P2109 style=SecH2 -->
11.9.1　多阶递归未来推演

<!-- source-paragraph:V82-P2110 style=BodyCJK -->
多步时间滚动、模拟状态再入和预期反身是三个正交维度。多步时间滚动在同一次运行中把状态沿时间推进；模拟再入把第一轮生成的某个模拟未来作为子运行起点；预期反身表示模拟中的行动者对更远未来或他人反应形成预期并改变当前策略。三者不得用一个“递归”词混写。

<!-- source-paragraph:V82-P2111 style=BodyCJK -->
本版把三阶设为默认探索上限：第一阶展开直接后果和竞争路径；第二阶考察第一阶状态如何改变行动集合、资源、圈层、反馈和适应；第三阶考察制度化、锁定、反转、跨圈层溢出以及生成条件本身的改变。三阶不是三个时间点，也不是自然阶段；条件不足时必须提前停止。

<!-- source-paragraph:V82-P2112 style=BodyCJK -->
总原则是：生成层可以大胆，状态层必须严格，证据层不得自我升级，行动层仍须另行授权。大胆只用于扩大合理的机制空间、竞争路径和低概率高后果分支，不能用于提高确定语气。

<!-- source-paragraph:V82-P2113 style=SecH3 -->
11.9.2　递归界面与谱系

<!-- source-paragraph:V82-P2114 style=BodyCJK -->
每次再入前都执行一次转义审计，记录当前阶次、父运行、父路径、父节点、模拟时点、本阶和累计时间窗、模型版本、继承假设、新增条件、保持、改变、折叠、遗漏、新增未知、目标有效变量、残差、同一性、返回路径和停止原因。模拟起点不得改写成当前现实。

<!-- source-paragraph:V82-P2115 style=BodyCJK -->
子运行必须继承父运行尚未解决的未知、损失和残差。选择某一假设分支只会缩小条件范围，不表示不确定性被现实材料消除；增加抽样次数只可能降低计算误差，不会提高关于现实结果的经验支持。

<!-- source-paragraph:V82-P2116 style=SecH3 -->
11.9.3　分支、合并与剪枝

<!-- source-paragraph:V82-P2117 style=BodyCJK -->
每阶至少保留当前主要路径、最强竞争路径、低概率高后果路径和残差出口。分支只来自可说明的条件、机制差异、行动者选择、外部扰动或类型化未知，不靠叙事趣味增加。

<!-- source-paragraph:V82-P2118 style=BodyCJK -->
只有对象同一性保持、关键状态在预定容差内等价、历史差异不改变后续转移、后续可用行动和约束一致时，分支才可合并。剪枝规则必须事前声明，并保留被剪分支、理由、可能的概率质量和伤害等级；低概率不能单独删除高后果路径。

<!-- source-paragraph:V82-P2119 style=SecH3 -->
11.9.4　提前停止

<!-- source-paragraph:V82-P2120 style=BodyCJK -->
出现对象或尺度同一性失效、关键假设无法继承、转移机制超出适用域、递归界面不闭合、分支爆炸且无区分信号、结果对微小变化全面反转、残差超过用途门槛、深一阶相对浅一阶和简单基线无增量、超出校准时间窗、触及权利或授权边界，或到达第三阶上限时，停止或降级。停止记录必须说明还能说什么和不能说什么。

<!-- source-paragraph:V82-P2121 style=SecH2 -->
11.10　推演运行的停止条件

<!-- source-paragraph:V82-P2122 style=BodyCJK -->
出现以下任一情况时，运行应暂停或降级：关键对象没有获得有限支持；事件事实地位不清；传播通道缺失；跨尺度映射失败；路径数量增长而没有区分性信号；模型对参数微小变化极度敏感；隐私或安全风险超过信息价值；推演被要求直接生成诊断、处罚或授权；简单基线已经表现相同或更好。

<!-- source-paragraph:V82-P2123 style=BodyCJK -->
停止不是失败掩盖，而是输出的一部分。停止记录应说明停在哪里、已获得什么、哪些未知阻止继续、下一项最有信息价值的观察是什么，以及继续推演会增加何种风险。

<!-- source-paragraph:V82-P2124 style=SecH2 -->
11.11　一个跨圈层级联示例

<!-- source-paragraph:V82-P2125 style=BodyCJK -->
继续第十部分的公开离职事件。起点快照显示：员工处于高工时和照护压力，团队信任下降，公司管理层关注声誉，职业社群提供外部机会，平台舆论尚未形成。事件是员工发布离职说明，内容真实性部分可核验、部分为个人叙述。

<!-- source-paragraph:V82-P2126 style=BodyCJK -->
直接效应包括团队收到信息、平台获得可传播文本、管理层面临回应压力。路径一：公司只做公开否认，短期外部舆论可能分叉为消退或放大；若内部成员把否认解释为压制，团队信任下降，经职业社群桥接出现更多离职。路径二：公司承认问题并启动可核验的资源与申诉调整；若实际执行，组织时钟上出现工时和流程变化，体验—意义时钟上信任恢复可能更慢。路径三：家庭照护条件变化降低员工退出后的压力，但这不直接改变团队状态，除非员工继续桥接信息或资源。

<!-- source-paragraph:V82-P2127 style=BodyCJK -->
早期信号可以是内部申诉数量、工时执行记录、成员公开表达、招聘和离职变化；反向信号可以是政策发布后没有实际资源变化、外部曝光下降但内部沉默增加、职业社群没有形成桥接。残差可能来自关键管理者状态、平台推荐机制或未观察的法律约束，这些只进入变量候选账本。

<!-- source-paragraph:V82-P2128 style=BodyCJK -->
该推演仍不能回答公司“应该”采取哪条路径。它提供条件后果和区分信号；前瞻登记、方案比较、规范前提和授权由下一部分处理。

<!-- source-paragraph:V82-P2129 style=SecH2 -->
11.12　本部分的输出

<!-- source-paragraph:V82-P2130 style=BodyCJK -->
一次合格推演输出应包含：冻结联合快照；事件类型与证据；机制和参数假设；更新步骤；路径图；每条路径的条件、时钟、支持状态、早期与反向信号；残差和变量候选；停止条件；结果回写计划；预测和行动的明确隔离声明。

<!-- source-paragraph:V82-P2131 style=BodyCJK -->
推演可以提高对后续的结构化准备，但它仍是条件性的。没有结果前登记、简单基线、校准和持续回写，不能据此宣称前瞻能力已经提高；没有规范与授权，不能据此宣称某项行动应当执行。

## Canonical Records

<!-- canonical-records:start -->
```json
{
  "paragraphs": [
    {
      "anchor": "V82-P1931",
      "ordinal": 1931,
      "style": "PartTitle",
      "text": "第十一部分　事件驱动的动态推演"
    },
    {
      "anchor": "V82-P1932",
      "ordinal": 1932,
      "style": "BodyCJK",
      "text": "动态推演回答的不是“世界接下来一定会怎样”，而是：从一个冻结的联合状态出发，在某个观察事件、情景事件或已授权行动发生后，哪些变量会先改变，影响沿什么通道传播，何处出现时延、阈值、反馈、跨圈层级联与分叉，哪些信号会提高或降低某条路径的支持度。"
    },
    {
      "anchor": "V82-P1933",
      "ordinal": 1933,
      "style": "SecH2",
      "text": "11.1　推演与叙事续写的区别"
    },
    {
      "anchor": "V82-P1934",
      "ordinal": 1934,
      "style": "BodyCJK",
      "text": "叙事续写可以凭连贯性选择一个后续；结构推演必须保留条件、通道、竞争路径和失败语义。若缺少关键变量，推演应停在未知或生成变量候选，而不是用最顺畅的故事补齐。若多个后续都与现有证据一致，就保持分叉；若路径无法比较，就不强制排序。"
    },
    {
      "anchor": "V82-P1935",
      "ordinal": 1935,
      "style": "BodyCJK",
      "text": "推演的最小输入为冻结快照、事件记录、机制假设、参数范围、时钟政策、传播政策、未知项和停止条件。最小输出为路径图、每一步状态差、支持状态、早期信号、反向信号、残差、变量候选和回写要求。"
    },
    {
      "anchor": "V82-P1936",
      "ordinal": 1936,
      "style": "TableHead",
      "text": "输入"
    },
    {
      "anchor": "V82-P1937",
      "ordinal": 1937,
      "style": "TableHead",
      "text": "必须冻结的内容"
    },
    {
      "anchor": "V82-P1938",
      "ordinal": 1938,
      "style": "TableHead",
      "text": "不冻结的后果"
    },
    {
      "anchor": "V82-P1939",
      "ordinal": 1939,
      "style": "TableText",
      "text": "联合快照"
    },
    {
      "anchor": "V82-P1940",
      "ordinal": 1940,
      "style": "TableText",
      "text": "行动者、圈层、关系、M/Ψ、时钟、证据截止"
    },
    {
      "anchor": "V82-P1941",
      "ordinal": 1941,
      "style": "TableText",
      "text": "结果后改写起点"
    },
    {
      "anchor": "V82-P1942",
      "ordinal": 1942,
      "style": "TableText",
      "text": "事件"
    },
    {
      "anchor": "V82-P1943",
      "ordinal": 1943,
      "style": "TableText",
      "text": "类型、时间、来源、触达对象与通道"
    },
    {
      "anchor": "V82-P1944",
      "ordinal": 1944,
      "style": "TableText",
      "text": "把传闻、计划和事实混装"
    },
    {
      "anchor": "V82-P1945",
      "ordinal": 1945,
      "style": "TableText",
      "text": "机制"
    },
    {
      "anchor": "V82-P1946",
      "ordinal": 1946,
      "style": "TableText",
      "text": "方向、载体、时延、阈值、失效条件"
    },
    {
      "anchor": "V82-P1947",
      "ordinal": 1947,
      "style": "TableText",
      "text": "任意解释每个结果"
    },
    {
      "anchor": "V82-P1948",
      "ordinal": 1948,
      "style": "TableText",
      "text": "参数"
    },
    {
      "anchor": "V82-P1949",
      "ordinal": 1949,
      "style": "TableText",
      "text": "值、区间、等级或明确未知"
    },
    {
      "anchor": "V82-P1950",
      "ordinal": 1950,
      "style": "TableText",
      "text": "用伪精确掩盖不确定"
    },
    {
      "anchor": "V82-P1951",
      "ordinal": 1951,
      "style": "TableText",
      "text": "停止"
    },
    {
      "anchor": "V82-P1952",
      "ordinal": 1952,
      "style": "TableText",
      "text": "信息、风险、越界与资源条件"
    },
    {
      "anchor": "V82-P1953",
      "ordinal": 1953,
      "style": "TableText",
      "text": "无限制向后讲故事"
    },
    {
      "anchor": "V82-P1954",
      "ordinal": 1954,
      "style": "SecH2",
      "text": "11.2　事件合同"
    },
    {
      "anchor": "V82-P1955",
      "ordinal": 1955,
      "style": "BodyCJK",
      "text": "事件包括观察到、被报告、计划中、假设性和模拟五类。类型必须进入记录：被报告的事件可以影响相信它的人，但不能自动当作已发生；计划可能改变预期，却不等于执行；假设事件用于条件分析；模拟事件只属于模型运行，不能回写现实事实。"
    },
    {
      "anchor": "V82-P1956",
      "ordinal": 1956,
      "style": "BodyCJK",
      "text": "事件记录至少包含：事件 ID、发生时间或窗口、观察时间、来源、受影响行动者、受影响圈层、通道、直接变化、证据状态、争议、竞争解释、可逆性、持续时间和后续观测。"
    },
    {
      "anchor": "V82-P1957",
      "ordinal": 1957,
      "style": "TableHead",
      "text": "事件类型"
    },
    {
      "anchor": "V82-P1958",
      "ordinal": 1958,
      "style": "TableHead",
      "text": "可以进入哪种推演"
    },
    {
      "anchor": "V82-P1959",
      "ordinal": 1959,
      "style": "TableHead",
      "text": "事实地位"
    },
    {
      "anchor": "V82-P1960",
      "ordinal": 1960,
      "style": "TableHead",
      "text": "必须附加的限制"
    },
    {
      "anchor": "V82-P1961",
      "ordinal": 1961,
      "style": "TableText",
      "text": "观察到"
    },
    {
      "anchor": "V82-P1962",
      "ordinal": 1962,
      "style": "TableText",
      "text": "解释、回放、前向推演"
    },
    {
      "anchor": "V82-P1963",
      "ordinal": 1963,
      "style": "TableText",
      "text": "在观察合同内成立"
    },
    {
      "anchor": "V82-P1964",
      "ordinal": 1964,
      "style": "TableText",
      "text": "来源、遗漏和测量误差"
    },
    {
      "anchor": "V82-P1965",
      "ordinal": 1965,
      "style": "TableText",
      "text": "被报告"
    },
    {
      "anchor": "V82-P1966",
      "ordinal": 1966,
      "style": "TableText",
      "text": "信念传播和条件推演"
    },
    {
      "anchor": "V82-P1967",
      "ordinal": 1967,
      "style": "TableText",
      "text": "报告发生，不等于内容为真"
    },
    {
      "anchor": "V82-P1968",
      "ordinal": 1968,
      "style": "TableText",
      "text": "报告者位置、核验和争议"
    },
    {
      "anchor": "V82-P1969",
      "ordinal": 1969,
      "style": "TableText",
      "text": "计划中"
    },
    {
      "anchor": "V82-P1970",
      "ordinal": 1970,
      "style": "TableText",
      "text": "预期、准备与策略互动"
    },
    {
      "anchor": "V82-P1971",
      "ordinal": 1971,
      "style": "TableText",
      "text": "计划存在，不等于执行"
    },
    {
      "anchor": "V82-P1972",
      "ordinal": 1972,
      "style": "TableText",
      "text": "授权、资源和取消条件"
    },
    {
      "anchor": "V82-P1973",
      "ordinal": 1973,
      "style": "TableText",
      "text": "假设性"
    },
    {
      "anchor": "V82-P1974",
      "ordinal": 1974,
      "style": "TableText",
      "text": "反事实与情景比较"
    },
    {
      "anchor": "V82-P1975",
      "ordinal": 1975,
      "style": "TableText",
      "text": "非现实事实"
    },
    {
      "anchor": "V82-P1976",
      "ordinal": 1976,
      "style": "TableText",
      "text": "条件、目的和可实现性"
    },
    {
      "anchor": "V82-P1977",
      "ordinal": 1977,
      "style": "TableText",
      "text": "模拟"
    },
    {
      "anchor": "V82-P1978",
      "ordinal": 1978,
      "style": "TableText",
      "text": "模型内部路径展开"
    },
    {
      "anchor": "V82-P1979",
      "ordinal": 1979,
      "style": "TableText",
      "text": "仅模型状态"
    },
    {
      "anchor": "V82-P1980",
      "ordinal": 1980,
      "style": "TableText",
      "text": "模型版本、参数和禁止外推"
    },
    {
      "anchor": "V82-P1981",
      "ordinal": 1981,
      "style": "SecH2",
      "text": "11.3　联合状态更新式"
    },
    {
      "anchor": "V82-P1982",
      "ordinal": 1982,
      "style": "BodyCJK",
      "text": "联合状态可写为："
    },
    {
      "anchor": "V82-P1983",
      "ordinal": 1983,
      "style": "BodyCJK",
      "text": "Ω(t) = <A(t), C(t), R(t), M(t), Ψ(t), Q(t), E≤t, SP(t), W(t), K(t)>。"
    },
    {
      "anchor": "V82-P1984",
      "ordinal": 1984,
      "style": "BodyCJK",
      "text": "一次更新可写为："
    },
    {
      "anchor": "V82-P1985",
      "ordinal": 1985,
      "style": "BodyCJK",
      "text": "Ω(t+Δ) = F[Ω(t), e(t), u(t), ξ(t) | θ, h]。"
    },
    {
      "anchor": "V82-P1986",
      "ordinal": 1986,
      "style": "BodyCJK",
      "text": "e(t) 是事件，u(t) 是已获外部授权且实际发生的行动，ξ(t) 是外生扰动或未建模残差，θ 是冻结的机制与参数假设，h 是历史项。这个式子只规定记录责任，不宣称存在唯一真实的 F，也不允许用函数符号替代具体机制。"
    },
    {
      "anchor": "V82-P1987",
      "ordinal": 1987,
      "style": "BodyCJK",
      "text": "每次更新都要区分：直接观察的状态差；由机制合同支持的推断；为探索路径设定的情景值；尚未解释的残差。四者在后续路径中保持来源，不因共同出现在一个快照中而获得相同证据地位。"
    },
    {
      "anchor": "V82-P1988",
      "ordinal": 1988,
      "style": "SecH2",
      "text": "11.4　九步推演闭环"
    },
    {
      "anchor": "V82-P1989",
      "ordinal": 1989,
      "style": "SecH3",
      "text": "11.4.1　第一步：冻结当前状态"
    },
    {
      "anchor": "V82-P1990",
      "ordinal": 1990,
      "style": "BodyCJK",
      "text": "记录证据截止、对象、变量、未知、争议和模型版本。截止后获得的信息不能倒灌到起点；若需使用，建立新运行版本。"
    },
    {
      "anchor": "V82-P1991",
      "ordinal": 1991,
      "style": "SecH3",
      "text": "11.4.2　第二步：识别行动者与圈层"
    },
    {
      "anchor": "V82-P1992",
      "ordinal": 1992,
      "style": "BodyCJK",
      "text": "调用第九、十部分。圈层不足以获得对象支持时保留候选分组；人格不足以获得支持时保留变量候选。不能为了使图完整而强行实体化。"
    },
    {
      "anchor": "V82-P1993",
      "ordinal": 1993,
      "style": "SecH3",
      "text": "11.4.3　第三步：分离双通道条件"
    },
    {
      "anchor": "V82-P1994",
      "ordinal": 1994,
      "style": "BodyCJK",
      "text": "把物质条件和体验—意义条件分别列出，并声明可能的跨通道桥。若只有一种条件有证据，另一种保持未知，不用对称假设补齐。"
    },
    {
      "anchor": "V82-P1995",
      "ordinal": 1995,
      "style": "SecH3",
      "text": "11.4.4　第四步：声明时钟、阈值、容量与时延"
    },
    {
      "anchor": "V82-P1996",
      "ordinal": 1996,
      "style": "BodyCJK",
      "text": "每个变量标明更新时钟。通道若有容量、延迟、损耗、饱和、反转或恢复窗口，应在传播前登记。"
    },
    {
      "anchor": "V82-P1997",
      "ordinal": 1997,
      "style": "SecH3",
      "text": "11.4.5　第五步：注入事件或行动"
    },
    {
      "anchor": "V82-P1998",
      "ordinal": 1998,
      "style": "BodyCJK",
      "text": "一次运行可以包含多个按时间排序的事件，但每个事件必须保留独立记录。行动必须有外部授权引用；没有授权时只能作为假设情景，而不能写成待执行指令。"
    },
    {
      "anchor": "V82-P1999",
      "ordinal": 1999,
      "style": "SecH3",
      "text": "11.4.6　第六步：沿已声明通道传播"
    },
    {
      "anchor": "V82-P2000",
      "ordinal": 2000,
      "style": "BodyCJK",
      "text": "先记录直接效应，再记录返回信号、间接效应和跨圈层级联。没有通道的影响保持候选，不因相关同时出现而连接。"
    },
    {
      "anchor": "V82-P2001",
      "ordinal": 2001,
      "style": "SecH3",
      "text": "11.4.7　第七步：在分叉点生成路径"
    },
    {
      "anchor": "V82-P2002",
      "ordinal": 2002,
      "style": "BodyCJK",
      "text": "条件、阈值、行动者选择、外部扰动或机制不确定都可能产生分叉。互斥路径分开；可以同时发生的路径保留并行；只有合并条件明确时才建立汇合节点。"
    },
    {
      "anchor": "V82-P2003",
      "ordinal": 2003,
      "style": "SecH3",
      "text": "11.4.8　第八步：登记信号、残差与变量候选"
    },
    {
      "anchor": "V82-P2004",
      "ordinal": 2004,
      "style": "BodyCJK",
      "text": "每条路径列出早期信号和反向信号。无法由当前变量解释的状态差进入残差；残差可以触发变量候选账本，但不能自动生成现实取值。"
    },
    {
      "anchor": "V82-P2005",
      "ordinal": 2005,
      "style": "SecH3",
      "text": "11.4.9　第九步：结果回写"
    },
    {
      "anchor": "V82-P2006",
      "ordinal": 2006,
      "style": "BodyCJK",
      "text": "真实结果到来后追加记录：哪条路径得到支持，哪些时点偏离，简单基线是否更好，校准如何，哪些机制或变量应降级、分裂、修改边界或退役。回写不覆盖原运行。"
    },
    {
      "anchor": "V82-P2007",
      "ordinal": 2007,
      "style": "SecH2",
      "text": "11.5　传播、时延与阈值"
    },
    {
      "anchor": "V82-P2008",
      "ordinal": 2008,
      "style": "BodyCJK",
      "text": "传播至少区分信号到达和有效状态改变。信息被看到但没有改变后续转移，只登记到达；改变了信念但没有行动，登记体验—意义状态变化；改变了资源、行为、规则或关系，才登记相应结构变化。"
    },
    {
      "anchor": "V82-P2009",
      "ordinal": 2009,
      "style": "TableHead",
      "text": "传播要素"
    },
    {
      "anchor": "V82-P2010",
      "ordinal": 2010,
      "style": "TableHead",
      "text": "记录问题"
    },
    {
      "anchor": "V82-P2011",
      "ordinal": 2011,
      "style": "TableHead",
      "text": "可能的非线性"
    },
    {
      "anchor": "V82-P2012",
      "ordinal": 2012,
      "style": "TableText",
      "text": "通道"
    },
    {
      "anchor": "V82-P2013",
      "ordinal": 2013,
      "style": "TableText",
      "text": "什么载体把影响从源带到目标"
    },
    {
      "anchor": "V82-P2014",
      "ordinal": 2014,
      "style": "TableText",
      "text": "通道关闭、过滤或替代"
    },
    {
      "anchor": "V82-P2015",
      "ordinal": 2015,
      "style": "TableText",
      "text": "容量"
    },
    {
      "anchor": "V82-P2016",
      "ordinal": 2016,
      "style": "TableText",
      "text": "单位时间可承载多少"
    },
    {
      "anchor": "V82-P2017",
      "ordinal": 2017,
      "style": "TableText",
      "text": "饱和、拥堵、排队"
    },
    {
      "anchor": "V82-P2018",
      "ordinal": 2018,
      "style": "TableText",
      "text": "时延"
    },
    {
      "anchor": "V82-P2019",
      "ordinal": 2019,
      "style": "TableText",
      "text": "何时到达、何时产生效果"
    },
    {
      "anchor": "V82-P2020",
      "ordinal": 2020,
      "style": "TableText",
      "text": "延迟反馈、误判无效"
    },
    {
      "anchor": "V82-P2021",
      "ordinal": 2021,
      "style": "TableText",
      "text": "阈值"
    },
    {
      "anchor": "V82-P2022",
      "ordinal": 2022,
      "style": "TableText",
      "text": "达到什么条件才改变状态"
    },
    {
      "anchor": "V82-P2023",
      "ordinal": 2023,
      "style": "TableText",
      "text": "突变、迟滞、级联"
    },
    {
      "anchor": "V82-P2024",
      "ordinal": 2024,
      "style": "TableText",
      "text": "损耗"
    },
    {
      "anchor": "V82-P2025",
      "ordinal": 2025,
      "style": "TableText",
      "text": "传播中丢失或转化什么"
    },
    {
      "anchor": "V82-P2026",
      "ordinal": 2026,
      "style": "TableText",
      "text": "意义漂移、资源耗散"
    },
    {
      "anchor": "V82-P2027",
      "ordinal": 2027,
      "style": "TableText",
      "text": "方向"
    },
    {
      "anchor": "V82-P2028",
      "ordinal": 2028,
      "style": "TableText",
      "text": "影响是否对称"
    },
    {
      "anchor": "V82-P2029",
      "ordinal": 2029,
      "style": "TableText",
      "text": "单向依赖、反向抵消"
    },
    {
      "anchor": "V82-P2030",
      "ordinal": 2030,
      "style": "TableText",
      "text": "恢复"
    },
    {
      "anchor": "V82-P2031",
      "ordinal": 2031,
      "style": "TableText",
      "text": "冲击后如何回到或转到新状态"
    },
    {
      "anchor": "V82-P2032",
      "ordinal": 2032,
      "style": "TableText",
      "text": "弹性、累积损伤、锁定"
    },
    {
      "anchor": "V82-P2033",
      "ordinal": 2033,
      "style": "BodyCJK",
      "text": "同一事件经不同通道到达不同圈层时，效果可以相反。资源增加可能降低一个圈层的负荷，却提高另一个圈层的竞争；公开说明可能修复外部合法性，却激活内部羞耻或不信任。推演应逐通道记录，不能用净效应掩盖分配差异。"
    },
    {
      "anchor": "V82-P2034",
      "ordinal": 2034,
      "style": "SecH2",
      "text": "11.6　反馈与跨圈层级联"
    },
    {
      "anchor": "V82-P2035",
      "ordinal": 2035,
      "style": "BodyCJK",
      "text": "反馈要求先前状态或输出经返回通道改变后续状态、转移概率或约束。级联要求一个局部变化经成员重叠、桥接、共享资源、制度下行或网络传播触发其他圈层变化。两者都要有时间顺序和通道证据。"
    },
    {
      "anchor": "V82-P2036",
      "ordinal": 2036,
      "style": "TableHead",
      "text": "级联类型"
    },
    {
      "anchor": "V82-P2037",
      "ordinal": 2037,
      "style": "TableHead",
      "text": "典型链条"
    },
    {
      "anchor": "V82-P2038",
      "ordinal": 2038,
      "style": "TableHead",
      "text": "观察重点"
    },
    {
      "anchor": "V82-P2039",
      "ordinal": 2039,
      "style": "TableHead",
      "text": "停止条件"
    },
    {
      "anchor": "V82-P2040",
      "ordinal": 2040,
      "style": "TableText",
      "text": "成员级联"
    },
    {
      "anchor": "V82-P2041",
      "ordinal": 2041,
      "style": "TableText",
      "text": "重叠成员把行为、情绪或信息带入另一圈层"
    },
    {
      "anchor": "V82-P2042",
      "ordinal": 2042,
      "style": "TableText",
      "text": "真实传导而非共同背景"
    },
    {
      "anchor": "V82-P2043",
      "ordinal": 2043,
      "style": "TableText",
      "text": "成员不再参与或信息未被接收"
    },
    {
      "anchor": "V82-P2044",
      "ordinal": 2044,
      "style": "TableText",
      "text": "资源级联"
    },
    {
      "anchor": "V82-P2045",
      "ordinal": 2045,
      "style": "TableText",
      "text": "一个圈层占用、释放或重配资源"
    },
    {
      "anchor": "V82-P2046",
      "ordinal": 2046,
      "style": "TableText",
      "text": "会计边界、转换和损耗"
    },
    {
      "anchor": "V82-P2047",
      "ordinal": 2047,
      "style": "TableText",
      "text": "资源隔离或替代来源"
    },
    {
      "anchor": "V82-P2048",
      "ordinal": 2048,
      "style": "TableText",
      "text": "意义级联"
    },
    {
      "anchor": "V82-P2049",
      "ordinal": 2049,
      "style": "TableText",
      "text": "事件解释改变身份、合法性或信任"
    },
    {
      "anchor": "V82-P2050",
      "ordinal": 2050,
      "style": "TableText",
      "text": "不同位置的解释差异"
    },
    {
      "anchor": "V82-P2051",
      "ordinal": 2051,
      "style": "TableText",
      "text": "意义未改变行动或规则"
    },
    {
      "anchor": "V82-P2052",
      "ordinal": 2052,
      "style": "TableText",
      "text": "制度级联"
    },
    {
      "anchor": "V82-P2053",
      "ordinal": 2053,
      "style": "TableText",
      "text": "申诉、审计或事件改变规则并下行执行"
    },
    {
      "anchor": "V82-P2054",
      "ordinal": 2054,
      "style": "TableText",
      "text": "决定、执行和实际写回"
    },
    {
      "anchor": "V82-P2055",
      "ordinal": 2055,
      "style": "TableText",
      "text": "规则未落实或被局部抵消"
    },
    {
      "anchor": "V82-P2056",
      "ordinal": 2056,
      "style": "TableText",
      "text": "平台级联"
    },
    {
      "anchor": "V82-P2057",
      "ordinal": 2057,
      "style": "TableText",
      "text": "推荐、指标或公开评价放大传播"
    },
    {
      "anchor": "V82-P2058",
      "ordinal": 2058,
      "style": "TableText",
      "text": "算法、选择性可见和反身性"
    },
    {
      "anchor": "V82-P2059",
      "ordinal": 2059,
      "style": "TableText",
      "text": "曝光不再增长或受众不响应"
    },
    {
      "anchor": "V82-P2060",
      "ordinal": 2060,
      "style": "BodyCJK",
      "text": "级联不是规模越大越重要。小圈层可能通过关键桥接产生高影响，大圈层可能因通道阻断而没有有效传播。推演应关注位置、通道和阈值，而不是只看成员数量。"
    },
    {
      "anchor": "V82-P2061",
      "ordinal": 2061,
      "style": "SecH2",
      "text": "11.7　分叉路径图"
    },
    {
      "anchor": "V82-P2062",
      "ordinal": 2062,
      "style": "BodyCJK",
      "text": "路径节点至少包含父节点、条件集、触发事件或行动、状态差、受影响时钟、支持状态、概率或排序表达、早期信号、反向信号、下一节点和终止理由。路径图应是有向无环图；若现实出现循环反馈，用时间展开后的新节点表示，不能让一个节点在同一次运行中既是自己的原因又是结果。"
    },
    {
      "anchor": "V82-P2063",
      "ordinal": 2063,
      "style": "BodyCJK",
      "text": "分叉可由四类不确定产生：事实不确定、机制不确定、行动者选择和外生扰动。不同类型不应合并成一个模糊概率。事实不确定优先核验；机制不确定通过区分性观察；选择不确定保留策略与授权；外生扰动通过情景范围和韧性检查。"
    },
    {
      "anchor": "V82-P2064",
      "ordinal": 2064,
      "style": "TableHead",
      "text": "分叉来源"
    },
    {
      "anchor": "V82-P2065",
      "ordinal": 2065,
      "style": "TableHead",
      "text": "例子"
    },
    {
      "anchor": "V82-P2066",
      "ordinal": 2066,
      "style": "TableHead",
      "text": "合适输出"
    },
    {
      "anchor": "V82-P2067",
      "ordinal": 2067,
      "style": "TableHead",
      "text": "不合适输出"
    },
    {
      "anchor": "V82-P2068",
      "ordinal": 2068,
      "style": "TableText",
      "text": "事实"
    },
    {
      "anchor": "V82-P2069",
      "ordinal": 2069,
      "style": "TableText",
      "text": "事件是否真实发生"
    },
    {
      "anchor": "V82-P2070",
      "ordinal": 2070,
      "style": "TableText",
      "text": "核验前的条件路径"
    },
    {
      "anchor": "V82-P2071",
      "ordinal": 2071,
      "style": "TableText",
      "text": "选一个版本当事实"
    },
    {
      "anchor": "V82-P2072",
      "ordinal": 2072,
      "style": "TableText",
      "text": "机制"
    },
    {
      "anchor": "V82-P2073",
      "ordinal": 2073,
      "style": "TableText",
      "text": "沉默来自恐惧还是策略"
    },
    {
      "anchor": "V82-P2074",
      "ordinal": 2074,
      "style": "TableText",
      "text": "区分信号和并行路径"
    },
    {
      "anchor": "V82-P2075",
      "ordinal": 2075,
      "style": "TableText",
      "text": "用人格标签封口"
    },
    {
      "anchor": "V82-P2076",
      "ordinal": 2076,
      "style": "TableText",
      "text": "选择"
    },
    {
      "anchor": "V82-P2077",
      "ordinal": 2077,
      "style": "TableText",
      "text": "行动者合作、抵抗或退出"
    },
    {
      "anchor": "V82-P2078",
      "ordinal": 2078,
      "style": "TableText",
      "text": "各选择的条件与后果"
    },
    {
      "anchor": "V82-P2079",
      "ordinal": 2079,
      "style": "TableText",
      "text": "宣称自由选择可精确预测"
    },
    {
      "anchor": "V82-P2080",
      "ordinal": 2080,
      "style": "TableText",
      "text": "扰动"
    },
    {
      "anchor": "V82-P2081",
      "ordinal": 2081,
      "style": "TableText",
      "text": "政策、价格、灾害或技术变化"
    },
    {
      "anchor": "V82-P2082",
      "ordinal": 2082,
      "style": "TableText",
      "text": "压力情景与恢复条件"
    },
    {
      "anchor": "V82-P2083",
      "ordinal": 2083,
      "style": "TableText",
      "text": "把未建模残差归因于命运"
    },
    {
      "anchor": "V82-P2084",
      "ordinal": 2084,
      "style": "SecH2",
      "text": "11.8　变量候选账本"
    },
    {
      "anchor": "V82-P2085",
      "ordinal": 2085,
      "style": "BodyCJK",
      "text": "模型无法解释的残差不能被删除，也不能立即命名成真实变量。候选账本把“我们可能漏了什么”转成可检验任务。每个候选至少记录来源残差、名称、可能类型、可能通道、可观察含义、竞争候选、最小检验、隐私与风险、当前状态、证据、升级和拒绝条件。"
    },
    {
      "anchor": "V82-P2086",
      "ordinal": 2086,
      "style": "BodyCJK",
      "text": "候选状态包括提出、检验中、得到支持的候选、拒绝和退役。即使得到支持，它仍要进入相应对象或变量合同，不能直接变成稳定人格、有效圈层或因果机制。结果后提出的候选可以改善下一轮模型，不能回头支撑原预测。"
    },
    {
      "anchor": "V82-P2087",
      "ordinal": 2087,
      "style": "TableHead",
      "text": "候选来源"
    },
    {
      "anchor": "V82-P2088",
      "ordinal": 2088,
      "style": "TableHead",
      "text": "合法动作"
    },
    {
      "anchor": "V82-P2089",
      "ordinal": 2089,
      "style": "TableHead",
      "text": "必须避免"
    },
    {
      "anchor": "V82-P2090",
      "ordinal": 2090,
      "style": "TableText",
      "text": "系统残差"
    },
    {
      "anchor": "V82-P2091",
      "ordinal": 2091,
      "style": "TableText",
      "text": "提出多个竞争候选和区分性观察"
    },
    {
      "anchor": "V82-P2092",
      "ordinal": 2092,
      "style": "TableText",
      "text": "用一个神秘变量吸收全部误差"
    },
    {
      "anchor": "V82-P2093",
      "ordinal": 2093,
      "style": "TableText",
      "text": "当事人叙述"
    },
    {
      "anchor": "V82-P2094",
      "ordinal": 2094,
      "style": "TableText",
      "text": "保留其位置、含义和可核验部分"
    },
    {
      "anchor": "V82-P2095",
      "ordinal": 2095,
      "style": "TableText",
      "text": "自动降格为主观噪声或升格为事实全貌"
    },
    {
      "anchor": "V82-P2096",
      "ordinal": 2096,
      "style": "TableText",
      "text": "跨案例重复"
    },
    {
      "anchor": "V82-P2097",
      "ordinal": 2097,
      "style": "TableText",
      "text": "建立候选机制与外推边界"
    },
    {
      "anchor": "V82-P2098",
      "ordinal": 2098,
      "style": "TableText",
      "text": "把相似叙事当通用规律"
    },
    {
      "anchor": "V82-P2099",
      "ordinal": 2099,
      "style": "TableText",
      "text": "模型搜索"
    },
    {
      "anchor": "V82-P2100",
      "ordinal": 2100,
      "style": "TableText",
      "text": "预注册下一轮检验"
    },
    {
      "anchor": "V82-P2101",
      "ordinal": 2101,
      "style": "TableText",
      "text": "结果后择优报告"
    },
    {
      "anchor": "V82-P2102",
      "ordinal": 2102,
      "style": "TableText",
      "text": "AI 建议"
    },
    {
      "anchor": "V82-P2103",
      "ordinal": 2103,
      "style": "TableText",
      "text": "仅作为候选生成"
    },
    {
      "anchor": "V82-P2104",
      "ordinal": 2104,
      "style": "TableText",
      "text": "让 AI 输出验证现实或授权行动"
    },
    {
      "anchor": "V82-P2105",
      "ordinal": 2105,
      "style": "BodyCJK",
      "text": "框架只能主动识别当前变量集无法解释的残差，提出多个可区分的变量候选，并为每个候选设计风险可接受的最小检验；它不能自主决定候选在现实中为真。"
    },
    {
      "anchor": "V82-P2106",
      "ordinal": 2106,
      "style": "SecH2",
      "text": "11.9　情景、反事实与模拟"
    },
    {
      "anchor": "V82-P2107",
      "ordinal": 2107,
      "style": "BodyCJK",
      "text": "情景推演问“如果这些条件成立，会出现什么路径”；反事实问“若某个事件或机制不同，已发生结果可能如何变化”；模拟把明确规则和参数展开。三者都需要与事实描述分开。"
    },
    {
      "anchor": "V82-P2108",
      "ordinal": 2108,
      "style": "BodyCJK",
      "text": "反事实尤其需要可比条件。删除一个事件时，还要说明哪些后续状态、行动者信息和圈层关系随之改变；不能只删除不喜欢的原因而保留其全部后果。模拟的精度不能超过输入和机制证据，参数未知时使用区间、等级或敏感性分析，不生成没有依据的小数点。"
    },
    {
      "anchor": "V82-P2109",
      "ordinal": 2109,
      "style": "SecH2",
      "text": "11.9.1　多阶递归未来推演"
    },
    {
      "anchor": "V82-P2110",
      "ordinal": 2110,
      "style": "BodyCJK",
      "text": "多步时间滚动、模拟状态再入和预期反身是三个正交维度。多步时间滚动在同一次运行中把状态沿时间推进；模拟再入把第一轮生成的某个模拟未来作为子运行起点；预期反身表示模拟中的行动者对更远未来或他人反应形成预期并改变当前策略。三者不得用一个“递归”词混写。"
    },
    {
      "anchor": "V82-P2111",
      "ordinal": 2111,
      "style": "BodyCJK",
      "text": "本版把三阶设为默认探索上限：第一阶展开直接后果和竞争路径；第二阶考察第一阶状态如何改变行动集合、资源、圈层、反馈和适应；第三阶考察制度化、锁定、反转、跨圈层溢出以及生成条件本身的改变。三阶不是三个时间点，也不是自然阶段；条件不足时必须提前停止。"
    },
    {
      "anchor": "V82-P2112",
      "ordinal": 2112,
      "style": "BodyCJK",
      "text": "总原则是：生成层可以大胆，状态层必须严格，证据层不得自我升级，行动层仍须另行授权。大胆只用于扩大合理的机制空间、竞争路径和低概率高后果分支，不能用于提高确定语气。"
    },
    {
      "anchor": "V82-P2113",
      "ordinal": 2113,
      "style": "SecH3",
      "text": "11.9.2　递归界面与谱系"
    },
    {
      "anchor": "V82-P2114",
      "ordinal": 2114,
      "style": "BodyCJK",
      "text": "每次再入前都执行一次转义审计，记录当前阶次、父运行、父路径、父节点、模拟时点、本阶和累计时间窗、模型版本、继承假设、新增条件、保持、改变、折叠、遗漏、新增未知、目标有效变量、残差、同一性、返回路径和停止原因。模拟起点不得改写成当前现实。"
    },
    {
      "anchor": "V82-P2115",
      "ordinal": 2115,
      "style": "BodyCJK",
      "text": "子运行必须继承父运行尚未解决的未知、损失和残差。选择某一假设分支只会缩小条件范围，不表示不确定性被现实材料消除；增加抽样次数只可能降低计算误差，不会提高关于现实结果的经验支持。"
    },
    {
      "anchor": "V82-P2116",
      "ordinal": 2116,
      "style": "SecH3",
      "text": "11.9.3　分支、合并与剪枝"
    },
    {
      "anchor": "V82-P2117",
      "ordinal": 2117,
      "style": "BodyCJK",
      "text": "每阶至少保留当前主要路径、最强竞争路径、低概率高后果路径和残差出口。分支只来自可说明的条件、机制差异、行动者选择、外部扰动或类型化未知，不靠叙事趣味增加。"
    },
    {
      "anchor": "V82-P2118",
      "ordinal": 2118,
      "style": "BodyCJK",
      "text": "只有对象同一性保持、关键状态在预定容差内等价、历史差异不改变后续转移、后续可用行动和约束一致时，分支才可合并。剪枝规则必须事前声明，并保留被剪分支、理由、可能的概率质量和伤害等级；低概率不能单独删除高后果路径。"
    },
    {
      "anchor": "V82-P2119",
      "ordinal": 2119,
      "style": "SecH3",
      "text": "11.9.4　提前停止"
    },
    {
      "anchor": "V82-P2120",
      "ordinal": 2120,
      "style": "BodyCJK",
      "text": "出现对象或尺度同一性失效、关键假设无法继承、转移机制超出适用域、递归界面不闭合、分支爆炸且无区分信号、结果对微小变化全面反转、残差超过用途门槛、深一阶相对浅一阶和简单基线无增量、超出校准时间窗、触及权利或授权边界，或到达第三阶上限时，停止或降级。停止记录必须说明还能说什么和不能说什么。"
    },
    {
      "anchor": "V82-P2121",
      "ordinal": 2121,
      "style": "SecH2",
      "text": "11.10　推演运行的停止条件"
    },
    {
      "anchor": "V82-P2122",
      "ordinal": 2122,
      "style": "BodyCJK",
      "text": "出现以下任一情况时，运行应暂停或降级：关键对象没有获得有限支持；事件事实地位不清；传播通道缺失；跨尺度映射失败；路径数量增长而没有区分性信号；模型对参数微小变化极度敏感；隐私或安全风险超过信息价值；推演被要求直接生成诊断、处罚或授权；简单基线已经表现相同或更好。"
    },
    {
      "anchor": "V82-P2123",
      "ordinal": 2123,
      "style": "BodyCJK",
      "text": "停止不是失败掩盖，而是输出的一部分。停止记录应说明停在哪里、已获得什么、哪些未知阻止继续、下一项最有信息价值的观察是什么，以及继续推演会增加何种风险。"
    },
    {
      "anchor": "V82-P2124",
      "ordinal": 2124,
      "style": "SecH2",
      "text": "11.11　一个跨圈层级联示例"
    },
    {
      "anchor": "V82-P2125",
      "ordinal": 2125,
      "style": "BodyCJK",
      "text": "继续第十部分的公开离职事件。起点快照显示：员工处于高工时和照护压力，团队信任下降，公司管理层关注声誉，职业社群提供外部机会，平台舆论尚未形成。事件是员工发布离职说明，内容真实性部分可核验、部分为个人叙述。"
    },
    {
      "anchor": "V82-P2126",
      "ordinal": 2126,
      "style": "BodyCJK",
      "text": "直接效应包括团队收到信息、平台获得可传播文本、管理层面临回应压力。路径一：公司只做公开否认，短期外部舆论可能分叉为消退或放大；若内部成员把否认解释为压制，团队信任下降，经职业社群桥接出现更多离职。路径二：公司承认问题并启动可核验的资源与申诉调整；若实际执行，组织时钟上出现工时和流程变化，体验—意义时钟上信任恢复可能更慢。路径三：家庭照护条件变化降低员工退出后的压力，但这不直接改变团队状态，除非员工继续桥接信息或资源。"
    },
    {
      "anchor": "V82-P2127",
      "ordinal": 2127,
      "style": "BodyCJK",
      "text": "早期信号可以是内部申诉数量、工时执行记录、成员公开表达、招聘和离职变化；反向信号可以是政策发布后没有实际资源变化、外部曝光下降但内部沉默增加、职业社群没有形成桥接。残差可能来自关键管理者状态、平台推荐机制或未观察的法律约束，这些只进入变量候选账本。"
    },
    {
      "anchor": "V82-P2128",
      "ordinal": 2128,
      "style": "BodyCJK",
      "text": "该推演仍不能回答公司“应该”采取哪条路径。它提供条件后果和区分信号；前瞻登记、方案比较、规范前提和授权由下一部分处理。"
    },
    {
      "anchor": "V82-P2129",
      "ordinal": 2129,
      "style": "SecH2",
      "text": "11.12　本部分的输出"
    },
    {
      "anchor": "V82-P2130",
      "ordinal": 2130,
      "style": "BodyCJK",
      "text": "一次合格推演输出应包含：冻结联合快照；事件类型与证据；机制和参数假设；更新步骤；路径图；每条路径的条件、时钟、支持状态、早期与反向信号；残差和变量候选；停止条件；结果回写计划；预测和行动的明确隔离声明。"
    },
    {
      "anchor": "V82-P2131",
      "ordinal": 2131,
      "style": "BodyCJK",
      "text": "推演可以提高对后续的结构化准备，但它仍是条件性的。没有结果前登记、简单基线、校准和持续回写，不能据此宣称前瞻能力已经提高；没有规范与授权，不能据此宣称某项行动应当执行。"
    }
  ],
  "tables": [
    {
      "anchor": "V82-T042",
      "cell_paragraph_ordinals": [
        [
          [
            1936
          ],
          [
            1937
          ],
          [
            1938
          ]
        ],
        [
          [
            1939
          ],
          [
            1940
          ],
          [
            1941
          ]
        ],
        [
          [
            1942
          ],
          [
            1943
          ],
          [
            1944
          ]
        ],
        [
          [
            1945
          ],
          [
            1946
          ],
          [
            1947
          ]
        ],
        [
          [
            1948
          ],
          [
            1949
          ],
          [
            1950
          ]
        ],
        [
          [
            1951
          ],
          [
            1952
          ],
          [
            1953
          ]
        ]
      ],
      "ordinal": 42,
      "paragraph_ordinals": [
        1936,
        1937,
        1938,
        1939,
        1940,
        1941,
        1942,
        1943,
        1944,
        1945,
        1946,
        1947,
        1948,
        1949,
        1950,
        1951,
        1952,
        1953
      ],
      "rows": [
        [
          "输入",
          "必须冻结的内容",
          "不冻结的后果"
        ],
        [
          "联合快照",
          "行动者、圈层、关系、M/Ψ、时钟、证据截止",
          "结果后改写起点"
        ],
        [
          "事件",
          "类型、时间、来源、触达对象与通道",
          "把传闻、计划和事实混装"
        ],
        [
          "机制",
          "方向、载体、时延、阈值、失效条件",
          "任意解释每个结果"
        ],
        [
          "参数",
          "值、区间、等级或明确未知",
          "用伪精确掩盖不确定"
        ],
        [
          "停止",
          "信息、风险、越界与资源条件",
          "无限制向后讲故事"
        ]
      ]
    },
    {
      "anchor": "V82-T043",
      "cell_paragraph_ordinals": [
        [
          [
            1957
          ],
          [
            1958
          ],
          [
            1959
          ],
          [
            1960
          ]
        ],
        [
          [
            1961
          ],
          [
            1962
          ],
          [
            1963
          ],
          [
            1964
          ]
        ],
        [
          [
            1965
          ],
          [
            1966
          ],
          [
            1967
          ],
          [
            1968
          ]
        ],
        [
          [
            1969
          ],
          [
            1970
          ],
          [
            1971
          ],
          [
            1972
          ]
        ],
        [
          [
            1973
          ],
          [
            1974
          ],
          [
            1975
          ],
          [
            1976
          ]
        ],
        [
          [
            1977
          ],
          [
            1978
          ],
          [
            1979
          ],
          [
            1980
          ]
        ]
      ],
      "ordinal": 43,
      "paragraph_ordinals": [
        1957,
        1958,
        1959,
        1960,
        1961,
        1962,
        1963,
        1964,
        1965,
        1966,
        1967,
        1968,
        1969,
        1970,
        1971,
        1972,
        1973,
        1974,
        1975,
        1976,
        1977,
        1978,
        1979,
        1980
      ],
      "rows": [
        [
          "事件类型",
          "可以进入哪种推演",
          "事实地位",
          "必须附加的限制"
        ],
        [
          "观察到",
          "解释、回放、前向推演",
          "在观察合同内成立",
          "来源、遗漏和测量误差"
        ],
        [
          "被报告",
          "信念传播和条件推演",
          "报告发生，不等于内容为真",
          "报告者位置、核验和争议"
        ],
        [
          "计划中",
          "预期、准备与策略互动",
          "计划存在，不等于执行",
          "授权、资源和取消条件"
        ],
        [
          "假设性",
          "反事实与情景比较",
          "非现实事实",
          "条件、目的和可实现性"
        ],
        [
          "模拟",
          "模型内部路径展开",
          "仅模型状态",
          "模型版本、参数和禁止外推"
        ]
      ]
    },
    {
      "anchor": "V82-T044",
      "cell_paragraph_ordinals": [
        [
          [
            2009
          ],
          [
            2010
          ],
          [
            2011
          ]
        ],
        [
          [
            2012
          ],
          [
            2013
          ],
          [
            2014
          ]
        ],
        [
          [
            2015
          ],
          [
            2016
          ],
          [
            2017
          ]
        ],
        [
          [
            2018
          ],
          [
            2019
          ],
          [
            2020
          ]
        ],
        [
          [
            2021
          ],
          [
            2022
          ],
          [
            2023
          ]
        ],
        [
          [
            2024
          ],
          [
            2025
          ],
          [
            2026
          ]
        ],
        [
          [
            2027
          ],
          [
            2028
          ],
          [
            2029
          ]
        ],
        [
          [
            2030
          ],
          [
            2031
          ],
          [
            2032
          ]
        ]
      ],
      "ordinal": 44,
      "paragraph_ordinals": [
        2009,
        2010,
        2011,
        2012,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
        2019,
        2020,
        2021,
        2022,
        2023,
        2024,
        2025,
        2026,
        2027,
        2028,
        2029,
        2030,
        2031,
        2032
      ],
      "rows": [
        [
          "传播要素",
          "记录问题",
          "可能的非线性"
        ],
        [
          "通道",
          "什么载体把影响从源带到目标",
          "通道关闭、过滤或替代"
        ],
        [
          "容量",
          "单位时间可承载多少",
          "饱和、拥堵、排队"
        ],
        [
          "时延",
          "何时到达、何时产生效果",
          "延迟反馈、误判无效"
        ],
        [
          "阈值",
          "达到什么条件才改变状态",
          "突变、迟滞、级联"
        ],
        [
          "损耗",
          "传播中丢失或转化什么",
          "意义漂移、资源耗散"
        ],
        [
          "方向",
          "影响是否对称",
          "单向依赖、反向抵消"
        ],
        [
          "恢复",
          "冲击后如何回到或转到新状态",
          "弹性、累积损伤、锁定"
        ]
      ]
    },
    {
      "anchor": "V82-T045",
      "cell_paragraph_ordinals": [
        [
          [
            2036
          ],
          [
            2037
          ],
          [
            2038
          ],
          [
            2039
          ]
        ],
        [
          [
            2040
          ],
          [
            2041
          ],
          [
            2042
          ],
          [
            2043
          ]
        ],
        [
          [
            2044
          ],
          [
            2045
          ],
          [
            2046
          ],
          [
            2047
          ]
        ],
        [
          [
            2048
          ],
          [
            2049
          ],
          [
            2050
          ],
          [
            2051
          ]
        ],
        [
          [
            2052
          ],
          [
            2053
          ],
          [
            2054
          ],
          [
            2055
          ]
        ],
        [
          [
            2056
          ],
          [
            2057
          ],
          [
            2058
          ],
          [
            2059
          ]
        ]
      ],
      "ordinal": 45,
      "paragraph_ordinals": [
        2036,
        2037,
        2038,
        2039,
        2040,
        2041,
        2042,
        2043,
        2044,
        2045,
        2046,
        2047,
        2048,
        2049,
        2050,
        2051,
        2052,
        2053,
        2054,
        2055,
        2056,
        2057,
        2058,
        2059
      ],
      "rows": [
        [
          "级联类型",
          "典型链条",
          "观察重点",
          "停止条件"
        ],
        [
          "成员级联",
          "重叠成员把行为、情绪或信息带入另一圈层",
          "真实传导而非共同背景",
          "成员不再参与或信息未被接收"
        ],
        [
          "资源级联",
          "一个圈层占用、释放或重配资源",
          "会计边界、转换和损耗",
          "资源隔离或替代来源"
        ],
        [
          "意义级联",
          "事件解释改变身份、合法性或信任",
          "不同位置的解释差异",
          "意义未改变行动或规则"
        ],
        [
          "制度级联",
          "申诉、审计或事件改变规则并下行执行",
          "决定、执行和实际写回",
          "规则未落实或被局部抵消"
        ],
        [
          "平台级联",
          "推荐、指标或公开评价放大传播",
          "算法、选择性可见和反身性",
          "曝光不再增长或受众不响应"
        ]
      ]
    },
    {
      "anchor": "V82-T046",
      "cell_paragraph_ordinals": [
        [
          [
            2064
          ],
          [
            2065
          ],
          [
            2066
          ],
          [
            2067
          ]
        ],
        [
          [
            2068
          ],
          [
            2069
          ],
          [
            2070
          ],
          [
            2071
          ]
        ],
        [
          [
            2072
          ],
          [
            2073
          ],
          [
            2074
          ],
          [
            2075
          ]
        ],
        [
          [
            2076
          ],
          [
            2077
          ],
          [
            2078
          ],
          [
            2079
          ]
        ],
        [
          [
            2080
          ],
          [
            2081
          ],
          [
            2082
          ],
          [
            2083
          ]
        ]
      ],
      "ordinal": 46,
      "paragraph_ordinals": [
        2064,
        2065,
        2066,
        2067,
        2068,
        2069,
        2070,
        2071,
        2072,
        2073,
        2074,
        2075,
        2076,
        2077,
        2078,
        2079,
        2080,
        2081,
        2082,
        2083
      ],
      "rows": [
        [
          "分叉来源",
          "例子",
          "合适输出",
          "不合适输出"
        ],
        [
          "事实",
          "事件是否真实发生",
          "核验前的条件路径",
          "选一个版本当事实"
        ],
        [
          "机制",
          "沉默来自恐惧还是策略",
          "区分信号和并行路径",
          "用人格标签封口"
        ],
        [
          "选择",
          "行动者合作、抵抗或退出",
          "各选择的条件与后果",
          "宣称自由选择可精确预测"
        ],
        [
          "扰动",
          "政策、价格、灾害或技术变化",
          "压力情景与恢复条件",
          "把未建模残差归因于命运"
        ]
      ]
    },
    {
      "anchor": "V82-T047",
      "cell_paragraph_ordinals": [
        [
          [
            2087
          ],
          [
            2088
          ],
          [
            2089
          ]
        ],
        [
          [
            2090
          ],
          [
            2091
          ],
          [
            2092
          ]
        ],
        [
          [
            2093
          ],
          [
            2094
          ],
          [
            2095
          ]
        ],
        [
          [
            2096
          ],
          [
            2097
          ],
          [
            2098
          ]
        ],
        [
          [
            2099
          ],
          [
            2100
          ],
          [
            2101
          ]
        ],
        [
          [
            2102
          ],
          [
            2103
          ],
          [
            2104
          ]
        ]
      ],
      "ordinal": 47,
      "paragraph_ordinals": [
        2087,
        2088,
        2089,
        2090,
        2091,
        2092,
        2093,
        2094,
        2095,
        2096,
        2097,
        2098,
        2099,
        2100,
        2101,
        2102,
        2103,
        2104
      ],
      "rows": [
        [
          "候选来源",
          "合法动作",
          "必须避免"
        ],
        [
          "系统残差",
          "提出多个竞争候选和区分性观察",
          "用一个神秘变量吸收全部误差"
        ],
        [
          "当事人叙述",
          "保留其位置、含义和可核验部分",
          "自动降格为主观噪声或升格为事实全貌"
        ],
        [
          "跨案例重复",
          "建立候选机制与外推边界",
          "把相似叙事当通用规律"
        ],
        [
          "模型搜索",
          "预注册下一轮检验",
          "结果后择优报告"
        ],
        [
          "AI 建议",
          "仅作为候选生成",
          "让 AI 输出验证现实或授权行动"
        ]
      ]
    }
  ]
}
```
<!-- canonical-records:end -->
