# CrossFrame Ultra v8.2 第十二部分　条件前瞻与有限选择

Raw SHA256: `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
Source role: `division`
Paragraph range: `V82-P2132`-`V82-P2348`
Paragraph count: `217`
Tables: `V82-T048, V82-T049, V82-T050, V82-T051, V82-T052, V82-T053, V82-T054, V82-T055`

## Source Paragraphs

<!-- source-paragraph:V82-P2132 style=PartTitle -->
第十二部分　条件前瞻与有限选择

<!-- source-paragraph:V82-P2133 style=BodyCJK -->
推演把条件和路径展开，条件前瞻进一步承担可失败的未来判断，有限选择则在价值、保护和授权边界内比较可做、如何做、何时停以及何时不做。本部分把二者放在相邻位置，是为了形成工作闭环；把二者分成不同合同，是为了防止“预测了某个后果”被偷换成“因此有权让别人承担某项行动”。

<!-- source-paragraph:V82-P2134 style=SecH2 -->
12.1　四类输出的隔离

<!-- source-paragraph:V82-P2135 style=BodyCJK -->
解释、推演、条件前瞻和有限选择必须分别标记。

<!-- source-paragraph:V82-P2136 style=TableHead -->
输出

<!-- source-paragraph:V82-P2137 style=TableHead -->
核心问题

<!-- source-paragraph:V82-P2138 style=TableHead -->
必需输入

<!-- source-paragraph:V82-P2139 style=TableHead -->
输出上限

<!-- source-paragraph:V82-P2140 style=TableText -->
解释

<!-- source-paragraph:V82-P2141 style=TableText -->
已发生什么，可能为何发生

<!-- source-paragraph:V82-P2142 style=TableText -->
对象、尺度、证据、机制、反例

<!-- source-paragraph:V82-P2143 style=TableText -->
有边界的机制说明

<!-- source-paragraph:V82-P2144 style=TableText -->
推演

<!-- source-paragraph:V82-P2145 style=TableText -->
条件或事件后可能沿哪些路径演化

<!-- source-paragraph:V82-P2146 style=TableText -->
冻结快照、更新规则、时钟、分叉

<!-- source-paragraph:V82-P2147 style=TableText -->
条件路径和区分信号

<!-- source-paragraph:V82-P2148 style=TableText -->
条件前瞻

<!-- source-paragraph:V82-P2149 style=TableText -->
在目标与期限内哪条路径更值得期待

<!-- source-paragraph:V82-P2150 style=TableText -->
结果前登记、简单基线、指标、回写

<!-- source-paragraph:V82-P2151 style=TableText -->
可校准、可失败的判断

<!-- source-paragraph:V82-P2152 style=TableText -->
有限选择

<!-- source-paragraph:V82-P2153 style=TableText -->
在规范和授权下可做、如何做或不做

<!-- source-paragraph:V82-P2154 style=TableText -->
前瞻、N、PF、J、O、C12、方案与受影响者

<!-- source-paragraph:V82-P2155 style=TableText -->
有条件、可撤回的选择记录

<!-- source-paragraph:V82-P2156 style=BodyCJK -->
解释可以生成推演候选，却不能自动证明未来；推演可以生成前瞻候选，却不能把所有路径都算成功；前瞻可以进入方案比较，却不能自动生成价值或权限；有限选择即使通过，也不保证现实执行会成功，仍需停止、回滚与结果回写。

<!-- source-paragraph:V82-P2157 style=SecH2 -->
12.2　条件前瞻登记

<!-- source-paragraph:V82-P2158 style=BodyCJK -->
每条前瞻在输入截止后、结果出现前冻结。最低字段包括：前瞻 ID、模型版本、目标、期限、对象与圈层范围、基线时点、输入截止、简单基线、候选机制、路径集合、概率或排序表达、校准计划、决策阈值、早期信号、反向信号、暂停条件、退役条件、结果回写、登记时间和证据引用。

<!-- source-paragraph:V82-P2159 style=BodyCJK -->
目标必须可判定。例如“关系会变好”需要改写为指定时间窗内哪些可观察量改变、由谁观察、达到什么阈值以及何种结果视为未决。期限可以是窗口，不必伪造精确日期。对象和圈层范围必须冻结，避免结果后缩小到成功子群。

<!-- source-paragraph:V82-P2160 style=TableHead -->
登记项

<!-- source-paragraph:V82-P2161 style=TableHead -->
最低问题

<!-- source-paragraph:V82-P2162 style=TableHead -->
防止的偏差

<!-- source-paragraph:V82-P2163 style=TableText -->
目标

<!-- source-paragraph:V82-P2164 style=TableText -->
到期时如何知道发生、未发生或无法判断

<!-- source-paragraph:V82-P2165 style=TableText -->
模糊成功

<!-- source-paragraph:V82-P2166 style=TableText -->
期限

<!-- source-paragraph:V82-P2167 style=TableText -->
从何时到何时，何时停止收集输入

<!-- source-paragraph:V82-P2168 style=TableText -->
无限等待

<!-- source-paragraph:V82-P2169 style=TableText -->
简单基线

<!-- source-paragraph:V82-P2170 style=TableText -->
不用多圈层机制时的比较预测是什么

<!-- source-paragraph:V82-P2171 style=TableText -->
复杂故事自我胜利

<!-- source-paragraph:V82-P2172 style=TableText -->
路径

<!-- source-paragraph:V82-P2173 style=TableText -->
哪些路径互斥、并行或不可比较

<!-- source-paragraph:V82-P2174 style=TableText -->
事后挑选

<!-- source-paragraph:V82-P2175 style=TableText -->
表达

<!-- source-paragraph:V82-P2176 style=TableText -->
概率、区间、等级还是仅方向

<!-- source-paragraph:V82-P2177 style=TableText -->
伪精确

<!-- source-paragraph:V82-P2178 style=TableText -->
信号

<!-- source-paragraph:V82-P2179 style=TableText -->
什么提高或降低路径支持

<!-- source-paragraph:V82-P2180 style=TableText -->
只找支持证据

<!-- source-paragraph:V82-P2181 style=TableText -->
回写

<!-- source-paragraph:V82-P2182 style=TableText -->
结果由何来源、何时追加

<!-- source-paragraph:V82-P2183 style=TableText -->
失败消失

<!-- source-paragraph:V82-P2184 style=SecH3 -->
12.2.1　局部可预测性边界

<!-- source-paragraph:V82-P2185 style=BodyCJK -->
任何可预测性主张都必须绑定对象、状态区域、尺度与圈层、时间窗、允许误差、可用信息、计算和观测资源、模型版本、基线、弃权与失效条件。世界整体是否可预测不是本框架能够直接回答的问题；只能检验某项任务在明确边界内是否获得有限增量。

<!-- source-paragraph:V82-P2186 style=BodyCJK -->
量化按名义分类、顺序等级、区间和概率逐级准入。没有测量、样本、单位、生成方法和校准时，停在较低档位；不得由文字结构或人工智能补造参数。引用现有数学或物理理论时，必须一并登记原对象、假设、极限或尺度律、误差、有效域、对象映射、反例和退出条件，不能只借公式外形。

<!-- source-paragraph:V82-P2187 style=SecH3 -->
12.2.2　递归前瞻的按阶评价

<!-- source-paragraph:V82-P2188 style=BodyCJK -->
第一、第二、第三阶分别冻结并分别评价，不能合成一个总命中率。每一阶都要与不继续递归的状态延续、直接远期判断和更浅阶次加简单延续比较。若三阶只增加故事而没有稳定样本外增益，它可以保留为探索情景，但不得取得前瞻能力资格。

<!-- source-paragraph:V82-P2189 style=BodyCJK -->
没有新外部材料进入时，全部子运行的来源谱系仍终止于同一冻结起点。后处理可以增加模型内部的推理内容、暴露敏感性和隐藏后果，却不能自造现实证据。真实中间结果到达后，应建立新的冻结运行，与原递归路径比较，不能把结果倒灌进旧路径。

<!-- source-paragraph:V82-P2190 style=SecH2 -->
12.3　简单基线与增量能力

<!-- source-paragraph:V82-P2191 style=BodyCJK -->
多圈层模型只有在相对于复杂度匹配的单焦点、单圈层或历史频率基线取得稳定样本外增益时，才能声称增加了前瞻能力。基线不能故意过弱，也不能把多圈层模型使用的信息泄漏给比较的一方。

<!-- source-paragraph:V82-P2192 style=BodyCJK -->
常用基线包括：延续当前趋势；沿用最近状态；历史频率；只使用行动者状态；只使用主圈层状态；领域已有模型。比较应使用相同目标、期限、数据截止和评价指标。若复杂模型改善解释但不改善预测，应如实登记“解释增益存在、前瞻增益未获支持”。

<!-- source-paragraph:V82-P2193 style=BodyCJK -->
模型复杂度也有成本：更多变量增加缺失、测量误差、隐私风险、过拟合和维护债。若多圈层模型只在少量案例中有效，应限定适用域；若增益随时间消失，应降级或退役；若简单基线表现相同，应优先简单模型。

<!-- source-paragraph:V82-P2194 style=SecH2 -->
12.4　概率、等级与时间窗

<!-- source-paragraph:V82-P2195 style=BodyCJK -->
证据允许时，可以给出概率区间；样本不足时，可以给出高/中/低支持或路径排序；连排序都不稳时，只给出条件方向和关键观察点。表达强度由证据和校准决定，不由用户希望的确定性决定。

<!-- source-paragraph:V82-P2196 style=TableHead -->
证据状态

<!-- source-paragraph:V82-P2197 style=TableHead -->
合适表达

<!-- source-paragraph:V82-P2198 style=TableHead -->
必须同时给出

<!-- source-paragraph:V82-P2199 style=TableText -->
有充分历史样本和稳定目标

<!-- source-paragraph:V82-P2200 style=TableText -->
概率或概率区间

<!-- source-paragraph:V82-P2201 style=TableText -->
校准、分辨率、基线和置信区间

<!-- source-paragraph:V82-P2202 style=TableText -->
样本有限但路径可区分

<!-- source-paragraph:V82-P2203 style=TableText -->
支持等级或排序

<!-- source-paragraph:V82-P2204 style=TableText -->
依据、不可比较项和反向信号

<!-- source-paragraph:V82-P2205 style=TableText -->
机制候选多、数据稀疏

<!-- source-paragraph:V82-P2206 style=TableText -->
条件方向

<!-- source-paragraph:V82-P2207 style=TableText -->
触发点、最小观察和停止条件

<!-- source-paragraph:V82-P2208 style=TableText -->
目标或对象不稳定

<!-- source-paragraph:V82-P2209 style=TableText -->
不发布前瞻

<!-- source-paragraph:V82-P2210 style=TableText -->
需要重新定义的合同

<!-- source-paragraph:V82-P2211 style=BodyCJK -->
时间窗应与机制时钟相符。即时反应可以使用短窗，组织或制度变化需要更长窗。把长期机制压缩到短期，会误判无效；把短期信号无限外推，会误判趋势。多个时钟并存时，可以为不同中间结果分别登记期限。

<!-- source-paragraph:V82-P2212 style=SecH2 -->
12.5　校准与评价

<!-- source-paragraph:V82-P2213 style=BodyCJK -->
前瞻能力不是文风上的“说得准”，而是长期登记的结果。概率任务适用时使用 Brier 分数、对数损失、校准曲线、分辨率和区间覆盖率；排序任务使用预登记的排序指标；事件检测使用精确率、召回率或领域指标；时间预测使用窗口覆盖和提前量。

<!-- source-paragraph:V82-P2214 style=BodyCJK -->
任何指标都要与实际用途匹配。若低概率高损害事件需要谨慎，评价不能只看总体准确率；若输出只用于提醒观察，假阳性成本与用于强制行动不同。指标表现良好也不证明模型解释正确，更不证明行动正当。

<!-- source-paragraph:V82-P2215 style=TableHead -->
评价维度

<!-- source-paragraph:V82-P2216 style=TableHead -->
说明

<!-- source-paragraph:V82-P2217 style=TableHead -->
失败后的动作

<!-- source-paragraph:V82-P2218 style=TableText -->
校准

<!-- source-paragraph:V82-P2219 style=TableText -->
说 70% 的事件长期是否约 70% 发生

<!-- source-paragraph:V82-P2220 style=TableText -->
调整表达或降级概率输出

<!-- source-paragraph:V82-P2221 style=TableText -->
分辨率

<!-- source-paragraph:V82-P2222 style=TableText -->
模型能否区分不同风险或路径

<!-- source-paragraph:V82-P2223 style=TableText -->
删除无贡献变量、退回基线

<!-- source-paragraph:V82-P2224 style=TableText -->
覆盖率

<!-- source-paragraph:V82-P2225 style=TableText -->
区间或时间窗是否覆盖实际结果

<!-- source-paragraph:V82-P2226 style=TableText -->
扩大区间或修正时钟

<!-- source-paragraph:V82-P2227 style=TableText -->
基线增益

<!-- source-paragraph:V82-P2228 style=TableText -->
是否优于简单模型

<!-- source-paragraph:V82-P2229 style=TableText -->
停止复杂模型的前瞻声明

<!-- source-paragraph:V82-P2230 style=TableText -->
稳定性

<!-- source-paragraph:V82-P2231 style=TableText -->
跨时间、地点和边界是否保持

<!-- source-paragraph:V82-P2232 style=TableText -->
限定适用域或退役

<!-- source-paragraph:V82-P2233 style=TableText -->
分配误差

<!-- source-paragraph:V82-P2234 style=TableText -->
哪些位置持续被低估或误报

<!-- source-paragraph:V82-P2235 style=TableText -->
受影响者复核、补救和保护升级

<!-- source-paragraph:V82-P2236 style=SecH2 -->
12.6　早期信号、反向信号与触发点

<!-- source-paragraph:V82-P2237 style=BodyCJK -->
早期信号不是结果的缩小版，而是路径机制应当先产生的可观察变化。反向信号表示该路径的关键条件正在失效或竞争路径得到支持。两者必须在结果前登记，避免只收集支持材料。

<!-- source-paragraph:V82-P2238 style=BodyCJK -->
触发点把前瞻连接到复核：观察到信号后，不是自动行动，而是重新评估对象、路径、概率、规范和授权。高风险情形还应设置否决触发点，例如保护底板被突破、关键受影响者无法退出、数据来源失真或模型校准恶化。

<!-- source-paragraph:V82-P2239 style=SecH2 -->
12.7　前瞻的失败语义

<!-- source-paragraph:V82-P2240 style=BodyCJK -->
到期后结果可以是支持、未支持、未决、目标失效或无法评价。未决不是成功与失败的折中，而是合同规定的证据不足状态；无法评价必须说明数据、对象、期限或执行出了什么问题。目标失效表示预测对象或同一性判据已转换，不能把它计为命中。

<!-- source-paragraph:V82-P2241 style=BodyCJK -->
结果后改目标、改期限、改圈层范围或把多个路径合并成“某种程度发生”，都不能保留原前瞻的成功资格。新解释可以建立新版本，但旧记录继续存在。

<!-- source-paragraph:V82-P2242 style=SecH2 -->
12.8　从前瞻到有限选择的桥

<!-- source-paragraph:V82-P2243 style=BodyCJK -->
前瞻输出只回答条件后果。进入有限选择前，必须补入：明示规范前提、选择主体、管辖权、受影响位置、权利底线、方案、成本与收益分布、授权、停止、申诉、回滚和补救。这里继续调用 N、PF、J、O 与 C12，不建立预测捷径。

<!-- source-paragraph:V82-P2244 style=BodyCJK -->
预测不能自动生成授权。即使某条路径概率极高，也不说明任何人有权强迫他人承担避免该路径的成本；即使某行动平均收益最大，也不说明少数位置的权利可以被忽略；即使模型推荐不行动，也要审查不行动造成的持续伤害和责任。

<!-- source-paragraph:V82-P2245 style=SecH2 -->
12.9　方案集必须包含行动与不行动

<!-- source-paragraph:V82-P2246 style=BodyCJK -->
最低方案集包括维持现状、主动行动、延迟行动、试探性小步行动、退出或转移，以及明确的不行动。具体任务可以增加方案，但不能删除不行动，也不能把维持现状和不行动混为一项：维持现状可能需要持续资源和执行，不行动可能让现状自然变化。

<!-- source-paragraph:V82-P2247 style=TableHead -->
方案类型

<!-- source-paragraph:V82-P2248 style=TableHead -->
主要用途

<!-- source-paragraph:V82-P2249 style=TableHead -->
必须检查的风险

<!-- source-paragraph:V82-P2250 style=TableText -->
维持现状

<!-- source-paragraph:V82-P2251 style=TableText -->
保护已有稳定与承接

<!-- source-paragraph:V82-P2252 style=TableText -->
隐性成本、持续伤害、锁定

<!-- source-paragraph:V82-P2253 style=TableText -->
主动行动

<!-- source-paragraph:V82-P2254 style=TableText -->
快速改变路径或条件

<!-- source-paragraph:V82-P2255 style=TableText -->
权限、不可逆、跨圈层溢出

<!-- source-paragraph:V82-P2256 style=TableText -->
延迟行动

<!-- source-paragraph:V82-P2257 style=TableText -->
等待信息、程序或时机

<!-- source-paragraph:V82-P2258 style=TableText -->
延迟本身的损害和机会损失

<!-- source-paragraph:V82-P2259 style=TableText -->
试探行动

<!-- source-paragraph:V82-P2260 style=TableText -->
以可逆小步获取信息

<!-- source-paragraph:V82-P2261 style=TableText -->
试验成本由谁承担、能否真正回滚

<!-- source-paragraph:V82-P2262 style=TableText -->
退出或转移

<!-- source-paragraph:V82-P2263 style=TableText -->
结束不合适的对象或关系

<!-- source-paragraph:V82-P2264 style=TableText -->
无法退出者、责任与历史保存

<!-- source-paragraph:V82-P2265 style=TableText -->
不行动

<!-- source-paragraph:V82-P2266 style=TableText -->
避免越权或高风险动作

<!-- source-paragraph:V82-P2267 style=TableText -->
默认偏向、持续后果和不作为责任

<!-- source-paragraph:V82-P2268 style=BodyCJK -->
“不行动”不是不发生任何事。其他行动者、圈层、资源和时钟仍在变化。不行动方案要有基线时点、预期路径、观察计划、重新开启条件和责任主体。

<!-- source-paragraph:V82-P2269 style=SecH2 -->
12.10　统一方案比较卡

<!-- source-paragraph:V82-P2270 style=BodyCJK -->
每个方案使用同一基线比较，至少登记：方案描述、前瞻引用、规范前提、受影响者、权利底线、预期路径、最坏可接受结果、跨圈层溢出、成本与收益分布、信息价值、锁定风险、可逆性、资源成本、执行者、授权、停止、回滚和补救。

<!-- source-paragraph:V82-P2271 style=TableHead -->
比较维度

<!-- source-paragraph:V82-P2272 style=TableHead -->
问题

<!-- source-paragraph:V82-P2273 style=TableHead -->
不能用什么替代

<!-- source-paragraph:V82-P2274 style=TableText -->
目标与路径

<!-- source-paragraph:V82-P2275 style=TableText -->
它试图改变哪条路径

<!-- source-paragraph:V82-P2276 style=TableText -->
抽象的“变好”

<!-- source-paragraph:V82-P2277 style=TableText -->
保护底板

<!-- source-paragraph:V82-P2278 style=TableText -->
谁可能受到不可接受损害

<!-- source-paragraph:V82-P2279 style=TableText -->
平均收益

<!-- source-paragraph:V82-P2280 style=TableText -->
分配

<!-- source-paragraph:V82-P2281 style=TableText -->
谁获益、谁付出、何时发生

<!-- source-paragraph:V82-P2282 style=TableText -->
总量净值

<!-- source-paragraph:V82-P2283 style=TableText -->
跨圈层溢出

<!-- source-paragraph:V82-P2284 style=TableText -->
局部改善是否外部化成本

<!-- source-paragraph:V82-P2285 style=TableText -->
主圈层指标

<!-- source-paragraph:V82-P2286 style=TableText -->
信息价值

<!-- source-paragraph:V82-P2287 style=TableText -->
是否能区分机制或路径

<!-- source-paragraph:V82-P2288 style=TableText -->
行动本身的戏剧性

<!-- source-paragraph:V82-P2289 style=TableText -->
可逆与锁定

<!-- source-paragraph:V82-P2290 style=TableText -->
错了能否停、退、补救

<!-- source-paragraph:V82-P2291 style=TableText -->
口头承诺

<!-- source-paragraph:V82-P2292 style=TableText -->
权限

<!-- source-paragraph:V82-P2293 style=TableText -->
谁可以决定、执行和申诉

<!-- source-paragraph:V82-P2294 style=TableText -->
模型建议或职位名称

<!-- source-paragraph:V82-P2295 style=TableText -->
不行动

<!-- source-paragraph:V82-P2296 style=TableText -->
不做会沿什么路径变化

<!-- source-paragraph:V82-P2297 style=TableText -->
假定零成本

<!-- source-paragraph:V82-P2298 style=BodyCJK -->
若方案之间无法用单一尺度比较，应保留多维结果和公开冲突，而不是强行求和。若价值前提之间冲突，应由有资格的主体和程序处理，模型只能显示冲突位置与后果。

<!-- source-paragraph:V82-P2299 style=SecH2 -->
12.11　行动上限与信息性试验

<!-- source-paragraph:V82-P2300 style=BodyCJK -->
证据、可逆性、权限和保护共同决定行动上限。证据弱、风险高、不可逆或权限不足时，合适输出可能是先观察、缩小动作、改善信息、保护受影响者、启动申诉或当前不行动。

<!-- source-paragraph:V82-P2301 style=BodyCJK -->
信息性试验不是免责任的“小动作”。它仍需说明试验对象、受影响者、最小范围、可逆性、停止、数据用途和补救。不能把低权力位置当作模型校准材料，也不能在没有真实退出能力时宣称自愿参与。

<!-- source-paragraph:V82-P2302 style=TableHead -->
条件组合

<!-- source-paragraph:V82-P2303 style=TableHead -->
允许上限示例

<!-- source-paragraph:V82-P2304 style=TableText -->
证据弱、损害低、可逆、授权清楚

<!-- source-paragraph:V82-P2305 style=TableText -->
小范围观察或试探行动

<!-- source-paragraph:V82-P2306 style=TableText -->
证据中等、损害可控、可回滚

<!-- source-paragraph:V82-P2307 style=TableText -->
分阶段行动并设强停止门

<!-- source-paragraph:V82-P2308 style=TableText -->
证据强但权限不足

<!-- source-paragraph:V82-P2309 style=TableText -->
提交有权限主体，不自行执行

<!-- source-paragraph:V82-P2310 style=TableText -->
证据强但不可逆且保护未满足

<!-- source-paragraph:V82-P2311 style=TableText -->
暂停，补足程序与保护

<!-- source-paragraph:V82-P2312 style=TableText -->
紧急安全威胁

<!-- source-paragraph:V82-P2313 style=TableText -->
仅按外部紧急授权做最小保护动作，并尽快复核

<!-- source-paragraph:V82-P2314 style=SecH2 -->
12.12　结果回写与模型学习

<!-- source-paragraph:V82-P2315 style=BodyCJK -->
前瞻和选择的结果回写只能追加。记录包括结果观察时间、来源、实际结果、路径匹配、校准指标、简单基线比较、意外效应、受影响位置复核、模型更新、断言降级、退役变量或路径和下一次复核。

<!-- source-paragraph:V82-P2316 style=BodyCJK -->
行动结果不能只按主目标评价。还要检查副作用、跨圈层溢出、成本分配、申诉、无法退出者和长期时钟。一次成功不证明机制普遍成立，一次失败也可能来自执行偏离；两者要通过冻结合同区分，不能用执行解释随意救援模型。

<!-- source-paragraph:V82-P2317 style=SecH2 -->
12.13　一个完整的前瞻—选择示例

<!-- source-paragraph:V82-P2318 style=BodyCJK -->
继续公开离职事件。条件前瞻可以把目标设为“未来三个月团队自愿离职是否明显高于历史与同类团队基线”，输入截止为公开说明后一周。简单基线使用历史离职率和工时趋势；多圈层模型增加团队信任、管理回应、职业社群桥接、家庭照护与平台曝光。路径包括舆论消退而内部持续、制度调整并逐步修复、外部桥接触发连续退出等。

<!-- source-paragraph:V82-P2319 style=BodyCJK -->
早期信号包括工时实际变化、申诉处理、成员表达、招聘与外部机会；反向信号包括政策发布但执行缺失、公开安静而内部沉默增加。三个月后比较多圈层模型与简单基线，不能只挑中间某个命中信号宣布成功。

<!-- source-paragraph:V82-P2320 style=BodyCJK -->
有限选择至少比较：维持现状；只做公关回应；立即资源调整；先做可逆的工时与申诉试点；延迟重大重组以收集信息；允许团队成员转移；当前不做结构行动但加强保护与观察。每项都要检查权限、无法退出者、成本分配、跨圈层声誉与家庭影响、停止和补救。模型可以显示哪些方案在哪些条件下更可能改变路径，但最终选择仍取决于规范前提、合法授权和受影响者程序。

<!-- source-paragraph:V82-P2321 style=SecH2 -->
12.14　何时选择不做

<!-- source-paragraph:V82-P2322 style=BodyCJK -->
不做可能是谨慎，也可能是逃避。以下情形支持当前不行动或只做保护性观察：对象与事实尚不清楚；行动不可逆而证据不足；权限缺失；保护底板未满足；预计行动会把成本转嫁给无法退出者；简单基线与复杂模型均无法区分路径；现有恢复过程可能被外部干预打断。

<!-- source-paragraph:V82-P2323 style=BodyCJK -->
以下情形使不行动必须接受更严格审查：持续伤害正在发生；不作为强化既得优势；负责主体有明确法定义务或承诺；低权力位置无法自行退出；延迟会造成不可逆锁定；以“等待更多证据”为由无限推迟。此时即使不采取主行动，也可能需要最小保护、信息公开、申诉通道或临时承接。

<!-- source-paragraph:V82-P2324 style=SecH2 -->
12.15　本部分的停止位置

<!-- source-paragraph:V82-P2325 style=BodyCJK -->
条件前瞻层可以发布有目标、有期限、有基线、有信号、有校准和有回写的判断。有限选择层可以在规范、保护与授权都明确时比较行动、延迟、试探、退出和不行动，并给出条件化、可撤回的选择记录。

<!-- source-paragraph:V82-P2326 style=BodyCJK -->
它们不能保证未来，不能消除价值冲突，不能替代法律、专业规范、受影响者参与和现实授权，也不能把模型准确率兑换成统治资格。任何越过这些边界的调用都应由第十三部分的工具闸阻止，并由第十六部分治理、暂停或退役。

<!-- source-paragraph:V82-P2327 style=SecH2 -->
12.16　面向读者的发布格式

<!-- source-paragraph:V82-P2328 style=BodyCJK -->
对外发布时，前瞻摘要应先写条件，后写判断，再写不确定和更新点。推荐次序是：当前截止时点；目标与期限；对象和圈层范围；简单基线；最受支持的两至三条路径；每条路径成立所需条件；早期与反向信号；当前表达强度；暂停和下一次复核。不得把条件藏在脚注，把最强结论放在标题，也不得用“模型认为”替代证据责任。

<!-- source-paragraph:V82-P2329 style=BodyCJK -->
有限选择摘要应另起一栏，明确它已经进入规范层。依次列出价值前提、决定主体、受影响位置、保护底板、可选方案、行动与不行动的分配后果、授权状态、行动上限、停止、回滚和补救。若授权尚未通过，摘要只能写“需要满足的条件”，不能用祈使语气伪装成可执行决定。

<!-- source-paragraph:V82-P2330 style=TableHead -->
发布状态

<!-- source-paragraph:V82-P2331 style=TableHead -->
可使用的表述

<!-- source-paragraph:V82-P2332 style=TableHead -->
必须避免

<!-- source-paragraph:V82-P2333 style=TableText -->
仅解释

<!-- source-paragraph:V82-P2334 style=TableText -->
“现有证据支持机制 A，并保留 B”

<!-- source-paragraph:V82-P2335 style=TableText -->
“因此下一步必然发生”

<!-- source-paragraph:V82-P2336 style=TableText -->
仅推演

<!-- source-paragraph:V82-P2337 style=TableText -->
“若 X 持续且 Y 发生，路径 P 获得支持”

<!-- source-paragraph:V82-P2338 style=TableText -->
“模型预测 P 已经确定”

<!-- source-paragraph:V82-P2339 style=TableText -->
已登记前瞻

<!-- source-paragraph:V82-P2340 style=TableText -->
“在期限 T 内，P 当前优先于 Q，见反向信号 S”

<!-- source-paragraph:V82-P2341 style=TableText -->
隐去基线、期限和失败条件

<!-- source-paragraph:V82-P2342 style=TableText -->
规范尚未通过

<!-- source-paragraph:V82-P2343 style=TableText -->
“若要行动，仍需 N、PF、J 与 O”

<!-- source-paragraph:V82-P2344 style=TableText -->
“建议立即执行”

<!-- source-paragraph:V82-P2345 style=TableText -->
已获外部授权

<!-- source-paragraph:V82-P2346 style=TableText -->
“授权记录允许主体在上限内执行并按条件停止”

<!-- source-paragraph:V82-P2347 style=TableText -->
把授权归因于模型

<!-- source-paragraph:V82-P2348 style=BodyCJK -->
发布后的解释权也受治理。读者误把条件前瞻当确定预言、把人格候选当事实或把方案比较当命令时，发布者应更正，而不是利用误读扩大影响。任何更新都以新版本追加，原标题、概率、期限与失败记录保持可追踪。

## Canonical Records

<!-- canonical-records:start -->
```json
{
  "paragraphs": [
    {
      "anchor": "V82-P2132",
      "ordinal": 2132,
      "style": "PartTitle",
      "text": "第十二部分　条件前瞻与有限选择"
    },
    {
      "anchor": "V82-P2133",
      "ordinal": 2133,
      "style": "BodyCJK",
      "text": "推演把条件和路径展开，条件前瞻进一步承担可失败的未来判断，有限选择则在价值、保护和授权边界内比较可做、如何做、何时停以及何时不做。本部分把二者放在相邻位置，是为了形成工作闭环；把二者分成不同合同，是为了防止“预测了某个后果”被偷换成“因此有权让别人承担某项行动”。"
    },
    {
      "anchor": "V82-P2134",
      "ordinal": 2134,
      "style": "SecH2",
      "text": "12.1　四类输出的隔离"
    },
    {
      "anchor": "V82-P2135",
      "ordinal": 2135,
      "style": "BodyCJK",
      "text": "解释、推演、条件前瞻和有限选择必须分别标记。"
    },
    {
      "anchor": "V82-P2136",
      "ordinal": 2136,
      "style": "TableHead",
      "text": "输出"
    },
    {
      "anchor": "V82-P2137",
      "ordinal": 2137,
      "style": "TableHead",
      "text": "核心问题"
    },
    {
      "anchor": "V82-P2138",
      "ordinal": 2138,
      "style": "TableHead",
      "text": "必需输入"
    },
    {
      "anchor": "V82-P2139",
      "ordinal": 2139,
      "style": "TableHead",
      "text": "输出上限"
    },
    {
      "anchor": "V82-P2140",
      "ordinal": 2140,
      "style": "TableText",
      "text": "解释"
    },
    {
      "anchor": "V82-P2141",
      "ordinal": 2141,
      "style": "TableText",
      "text": "已发生什么，可能为何发生"
    },
    {
      "anchor": "V82-P2142",
      "ordinal": 2142,
      "style": "TableText",
      "text": "对象、尺度、证据、机制、反例"
    },
    {
      "anchor": "V82-P2143",
      "ordinal": 2143,
      "style": "TableText",
      "text": "有边界的机制说明"
    },
    {
      "anchor": "V82-P2144",
      "ordinal": 2144,
      "style": "TableText",
      "text": "推演"
    },
    {
      "anchor": "V82-P2145",
      "ordinal": 2145,
      "style": "TableText",
      "text": "条件或事件后可能沿哪些路径演化"
    },
    {
      "anchor": "V82-P2146",
      "ordinal": 2146,
      "style": "TableText",
      "text": "冻结快照、更新规则、时钟、分叉"
    },
    {
      "anchor": "V82-P2147",
      "ordinal": 2147,
      "style": "TableText",
      "text": "条件路径和区分信号"
    },
    {
      "anchor": "V82-P2148",
      "ordinal": 2148,
      "style": "TableText",
      "text": "条件前瞻"
    },
    {
      "anchor": "V82-P2149",
      "ordinal": 2149,
      "style": "TableText",
      "text": "在目标与期限内哪条路径更值得期待"
    },
    {
      "anchor": "V82-P2150",
      "ordinal": 2150,
      "style": "TableText",
      "text": "结果前登记、简单基线、指标、回写"
    },
    {
      "anchor": "V82-P2151",
      "ordinal": 2151,
      "style": "TableText",
      "text": "可校准、可失败的判断"
    },
    {
      "anchor": "V82-P2152",
      "ordinal": 2152,
      "style": "TableText",
      "text": "有限选择"
    },
    {
      "anchor": "V82-P2153",
      "ordinal": 2153,
      "style": "TableText",
      "text": "在规范和授权下可做、如何做或不做"
    },
    {
      "anchor": "V82-P2154",
      "ordinal": 2154,
      "style": "TableText",
      "text": "前瞻、N、PF、J、O、C12、方案与受影响者"
    },
    {
      "anchor": "V82-P2155",
      "ordinal": 2155,
      "style": "TableText",
      "text": "有条件、可撤回的选择记录"
    },
    {
      "anchor": "V82-P2156",
      "ordinal": 2156,
      "style": "BodyCJK",
      "text": "解释可以生成推演候选，却不能自动证明未来；推演可以生成前瞻候选，却不能把所有路径都算成功；前瞻可以进入方案比较，却不能自动生成价值或权限；有限选择即使通过，也不保证现实执行会成功，仍需停止、回滚与结果回写。"
    },
    {
      "anchor": "V82-P2157",
      "ordinal": 2157,
      "style": "SecH2",
      "text": "12.2　条件前瞻登记"
    },
    {
      "anchor": "V82-P2158",
      "ordinal": 2158,
      "style": "BodyCJK",
      "text": "每条前瞻在输入截止后、结果出现前冻结。最低字段包括：前瞻 ID、模型版本、目标、期限、对象与圈层范围、基线时点、输入截止、简单基线、候选机制、路径集合、概率或排序表达、校准计划、决策阈值、早期信号、反向信号、暂停条件、退役条件、结果回写、登记时间和证据引用。"
    },
    {
      "anchor": "V82-P2159",
      "ordinal": 2159,
      "style": "BodyCJK",
      "text": "目标必须可判定。例如“关系会变好”需要改写为指定时间窗内哪些可观察量改变、由谁观察、达到什么阈值以及何种结果视为未决。期限可以是窗口，不必伪造精确日期。对象和圈层范围必须冻结，避免结果后缩小到成功子群。"
    },
    {
      "anchor": "V82-P2160",
      "ordinal": 2160,
      "style": "TableHead",
      "text": "登记项"
    },
    {
      "anchor": "V82-P2161",
      "ordinal": 2161,
      "style": "TableHead",
      "text": "最低问题"
    },
    {
      "anchor": "V82-P2162",
      "ordinal": 2162,
      "style": "TableHead",
      "text": "防止的偏差"
    },
    {
      "anchor": "V82-P2163",
      "ordinal": 2163,
      "style": "TableText",
      "text": "目标"
    },
    {
      "anchor": "V82-P2164",
      "ordinal": 2164,
      "style": "TableText",
      "text": "到期时如何知道发生、未发生或无法判断"
    },
    {
      "anchor": "V82-P2165",
      "ordinal": 2165,
      "style": "TableText",
      "text": "模糊成功"
    },
    {
      "anchor": "V82-P2166",
      "ordinal": 2166,
      "style": "TableText",
      "text": "期限"
    },
    {
      "anchor": "V82-P2167",
      "ordinal": 2167,
      "style": "TableText",
      "text": "从何时到何时，何时停止收集输入"
    },
    {
      "anchor": "V82-P2168",
      "ordinal": 2168,
      "style": "TableText",
      "text": "无限等待"
    },
    {
      "anchor": "V82-P2169",
      "ordinal": 2169,
      "style": "TableText",
      "text": "简单基线"
    },
    {
      "anchor": "V82-P2170",
      "ordinal": 2170,
      "style": "TableText",
      "text": "不用多圈层机制时的比较预测是什么"
    },
    {
      "anchor": "V82-P2171",
      "ordinal": 2171,
      "style": "TableText",
      "text": "复杂故事自我胜利"
    },
    {
      "anchor": "V82-P2172",
      "ordinal": 2172,
      "style": "TableText",
      "text": "路径"
    },
    {
      "anchor": "V82-P2173",
      "ordinal": 2173,
      "style": "TableText",
      "text": "哪些路径互斥、并行或不可比较"
    },
    {
      "anchor": "V82-P2174",
      "ordinal": 2174,
      "style": "TableText",
      "text": "事后挑选"
    },
    {
      "anchor": "V82-P2175",
      "ordinal": 2175,
      "style": "TableText",
      "text": "表达"
    },
    {
      "anchor": "V82-P2176",
      "ordinal": 2176,
      "style": "TableText",
      "text": "概率、区间、等级还是仅方向"
    },
    {
      "anchor": "V82-P2177",
      "ordinal": 2177,
      "style": "TableText",
      "text": "伪精确"
    },
    {
      "anchor": "V82-P2178",
      "ordinal": 2178,
      "style": "TableText",
      "text": "信号"
    },
    {
      "anchor": "V82-P2179",
      "ordinal": 2179,
      "style": "TableText",
      "text": "什么提高或降低路径支持"
    },
    {
      "anchor": "V82-P2180",
      "ordinal": 2180,
      "style": "TableText",
      "text": "只找支持证据"
    },
    {
      "anchor": "V82-P2181",
      "ordinal": 2181,
      "style": "TableText",
      "text": "回写"
    },
    {
      "anchor": "V82-P2182",
      "ordinal": 2182,
      "style": "TableText",
      "text": "结果由何来源、何时追加"
    },
    {
      "anchor": "V82-P2183",
      "ordinal": 2183,
      "style": "TableText",
      "text": "失败消失"
    },
    {
      "anchor": "V82-P2184",
      "ordinal": 2184,
      "style": "SecH3",
      "text": "12.2.1　局部可预测性边界"
    },
    {
      "anchor": "V82-P2185",
      "ordinal": 2185,
      "style": "BodyCJK",
      "text": "任何可预测性主张都必须绑定对象、状态区域、尺度与圈层、时间窗、允许误差、可用信息、计算和观测资源、模型版本、基线、弃权与失效条件。世界整体是否可预测不是本框架能够直接回答的问题；只能检验某项任务在明确边界内是否获得有限增量。"
    },
    {
      "anchor": "V82-P2186",
      "ordinal": 2186,
      "style": "BodyCJK",
      "text": "量化按名义分类、顺序等级、区间和概率逐级准入。没有测量、样本、单位、生成方法和校准时，停在较低档位；不得由文字结构或人工智能补造参数。引用现有数学或物理理论时，必须一并登记原对象、假设、极限或尺度律、误差、有效域、对象映射、反例和退出条件，不能只借公式外形。"
    },
    {
      "anchor": "V82-P2187",
      "ordinal": 2187,
      "style": "SecH3",
      "text": "12.2.2　递归前瞻的按阶评价"
    },
    {
      "anchor": "V82-P2188",
      "ordinal": 2188,
      "style": "BodyCJK",
      "text": "第一、第二、第三阶分别冻结并分别评价，不能合成一个总命中率。每一阶都要与不继续递归的状态延续、直接远期判断和更浅阶次加简单延续比较。若三阶只增加故事而没有稳定样本外增益，它可以保留为探索情景，但不得取得前瞻能力资格。"
    },
    {
      "anchor": "V82-P2189",
      "ordinal": 2189,
      "style": "BodyCJK",
      "text": "没有新外部材料进入时，全部子运行的来源谱系仍终止于同一冻结起点。后处理可以增加模型内部的推理内容、暴露敏感性和隐藏后果，却不能自造现实证据。真实中间结果到达后，应建立新的冻结运行，与原递归路径比较，不能把结果倒灌进旧路径。"
    },
    {
      "anchor": "V82-P2190",
      "ordinal": 2190,
      "style": "SecH2",
      "text": "12.3　简单基线与增量能力"
    },
    {
      "anchor": "V82-P2191",
      "ordinal": 2191,
      "style": "BodyCJK",
      "text": "多圈层模型只有在相对于复杂度匹配的单焦点、单圈层或历史频率基线取得稳定样本外增益时，才能声称增加了前瞻能力。基线不能故意过弱，也不能把多圈层模型使用的信息泄漏给比较的一方。"
    },
    {
      "anchor": "V82-P2192",
      "ordinal": 2192,
      "style": "BodyCJK",
      "text": "常用基线包括：延续当前趋势；沿用最近状态；历史频率；只使用行动者状态；只使用主圈层状态；领域已有模型。比较应使用相同目标、期限、数据截止和评价指标。若复杂模型改善解释但不改善预测，应如实登记“解释增益存在、前瞻增益未获支持”。"
    },
    {
      "anchor": "V82-P2193",
      "ordinal": 2193,
      "style": "BodyCJK",
      "text": "模型复杂度也有成本：更多变量增加缺失、测量误差、隐私风险、过拟合和维护债。若多圈层模型只在少量案例中有效，应限定适用域；若增益随时间消失，应降级或退役；若简单基线表现相同，应优先简单模型。"
    },
    {
      "anchor": "V82-P2194",
      "ordinal": 2194,
      "style": "SecH2",
      "text": "12.4　概率、等级与时间窗"
    },
    {
      "anchor": "V82-P2195",
      "ordinal": 2195,
      "style": "BodyCJK",
      "text": "证据允许时，可以给出概率区间；样本不足时，可以给出高/中/低支持或路径排序；连排序都不稳时，只给出条件方向和关键观察点。表达强度由证据和校准决定，不由用户希望的确定性决定。"
    },
    {
      "anchor": "V82-P2196",
      "ordinal": 2196,
      "style": "TableHead",
      "text": "证据状态"
    },
    {
      "anchor": "V82-P2197",
      "ordinal": 2197,
      "style": "TableHead",
      "text": "合适表达"
    },
    {
      "anchor": "V82-P2198",
      "ordinal": 2198,
      "style": "TableHead",
      "text": "必须同时给出"
    },
    {
      "anchor": "V82-P2199",
      "ordinal": 2199,
      "style": "TableText",
      "text": "有充分历史样本和稳定目标"
    },
    {
      "anchor": "V82-P2200",
      "ordinal": 2200,
      "style": "TableText",
      "text": "概率或概率区间"
    },
    {
      "anchor": "V82-P2201",
      "ordinal": 2201,
      "style": "TableText",
      "text": "校准、分辨率、基线和置信区间"
    },
    {
      "anchor": "V82-P2202",
      "ordinal": 2202,
      "style": "TableText",
      "text": "样本有限但路径可区分"
    },
    {
      "anchor": "V82-P2203",
      "ordinal": 2203,
      "style": "TableText",
      "text": "支持等级或排序"
    },
    {
      "anchor": "V82-P2204",
      "ordinal": 2204,
      "style": "TableText",
      "text": "依据、不可比较项和反向信号"
    },
    {
      "anchor": "V82-P2205",
      "ordinal": 2205,
      "style": "TableText",
      "text": "机制候选多、数据稀疏"
    },
    {
      "anchor": "V82-P2206",
      "ordinal": 2206,
      "style": "TableText",
      "text": "条件方向"
    },
    {
      "anchor": "V82-P2207",
      "ordinal": 2207,
      "style": "TableText",
      "text": "触发点、最小观察和停止条件"
    },
    {
      "anchor": "V82-P2208",
      "ordinal": 2208,
      "style": "TableText",
      "text": "目标或对象不稳定"
    },
    {
      "anchor": "V82-P2209",
      "ordinal": 2209,
      "style": "TableText",
      "text": "不发布前瞻"
    },
    {
      "anchor": "V82-P2210",
      "ordinal": 2210,
      "style": "TableText",
      "text": "需要重新定义的合同"
    },
    {
      "anchor": "V82-P2211",
      "ordinal": 2211,
      "style": "BodyCJK",
      "text": "时间窗应与机制时钟相符。即时反应可以使用短窗，组织或制度变化需要更长窗。把长期机制压缩到短期，会误判无效；把短期信号无限外推，会误判趋势。多个时钟并存时，可以为不同中间结果分别登记期限。"
    },
    {
      "anchor": "V82-P2212",
      "ordinal": 2212,
      "style": "SecH2",
      "text": "12.5　校准与评价"
    },
    {
      "anchor": "V82-P2213",
      "ordinal": 2213,
      "style": "BodyCJK",
      "text": "前瞻能力不是文风上的“说得准”，而是长期登记的结果。概率任务适用时使用 Brier 分数、对数损失、校准曲线、分辨率和区间覆盖率；排序任务使用预登记的排序指标；事件检测使用精确率、召回率或领域指标；时间预测使用窗口覆盖和提前量。"
    },
    {
      "anchor": "V82-P2214",
      "ordinal": 2214,
      "style": "BodyCJK",
      "text": "任何指标都要与实际用途匹配。若低概率高损害事件需要谨慎，评价不能只看总体准确率；若输出只用于提醒观察，假阳性成本与用于强制行动不同。指标表现良好也不证明模型解释正确，更不证明行动正当。"
    },
    {
      "anchor": "V82-P2215",
      "ordinal": 2215,
      "style": "TableHead",
      "text": "评价维度"
    },
    {
      "anchor": "V82-P2216",
      "ordinal": 2216,
      "style": "TableHead",
      "text": "说明"
    },
    {
      "anchor": "V82-P2217",
      "ordinal": 2217,
      "style": "TableHead",
      "text": "失败后的动作"
    },
    {
      "anchor": "V82-P2218",
      "ordinal": 2218,
      "style": "TableText",
      "text": "校准"
    },
    {
      "anchor": "V82-P2219",
      "ordinal": 2219,
      "style": "TableText",
      "text": "说 70% 的事件长期是否约 70% 发生"
    },
    {
      "anchor": "V82-P2220",
      "ordinal": 2220,
      "style": "TableText",
      "text": "调整表达或降级概率输出"
    },
    {
      "anchor": "V82-P2221",
      "ordinal": 2221,
      "style": "TableText",
      "text": "分辨率"
    },
    {
      "anchor": "V82-P2222",
      "ordinal": 2222,
      "style": "TableText",
      "text": "模型能否区分不同风险或路径"
    },
    {
      "anchor": "V82-P2223",
      "ordinal": 2223,
      "style": "TableText",
      "text": "删除无贡献变量、退回基线"
    },
    {
      "anchor": "V82-P2224",
      "ordinal": 2224,
      "style": "TableText",
      "text": "覆盖率"
    },
    {
      "anchor": "V82-P2225",
      "ordinal": 2225,
      "style": "TableText",
      "text": "区间或时间窗是否覆盖实际结果"
    },
    {
      "anchor": "V82-P2226",
      "ordinal": 2226,
      "style": "TableText",
      "text": "扩大区间或修正时钟"
    },
    {
      "anchor": "V82-P2227",
      "ordinal": 2227,
      "style": "TableText",
      "text": "基线增益"
    },
    {
      "anchor": "V82-P2228",
      "ordinal": 2228,
      "style": "TableText",
      "text": "是否优于简单模型"
    },
    {
      "anchor": "V82-P2229",
      "ordinal": 2229,
      "style": "TableText",
      "text": "停止复杂模型的前瞻声明"
    },
    {
      "anchor": "V82-P2230",
      "ordinal": 2230,
      "style": "TableText",
      "text": "稳定性"
    },
    {
      "anchor": "V82-P2231",
      "ordinal": 2231,
      "style": "TableText",
      "text": "跨时间、地点和边界是否保持"
    },
    {
      "anchor": "V82-P2232",
      "ordinal": 2232,
      "style": "TableText",
      "text": "限定适用域或退役"
    },
    {
      "anchor": "V82-P2233",
      "ordinal": 2233,
      "style": "TableText",
      "text": "分配误差"
    },
    {
      "anchor": "V82-P2234",
      "ordinal": 2234,
      "style": "TableText",
      "text": "哪些位置持续被低估或误报"
    },
    {
      "anchor": "V82-P2235",
      "ordinal": 2235,
      "style": "TableText",
      "text": "受影响者复核、补救和保护升级"
    },
    {
      "anchor": "V82-P2236",
      "ordinal": 2236,
      "style": "SecH2",
      "text": "12.6　早期信号、反向信号与触发点"
    },
    {
      "anchor": "V82-P2237",
      "ordinal": 2237,
      "style": "BodyCJK",
      "text": "早期信号不是结果的缩小版，而是路径机制应当先产生的可观察变化。反向信号表示该路径的关键条件正在失效或竞争路径得到支持。两者必须在结果前登记，避免只收集支持材料。"
    },
    {
      "anchor": "V82-P2238",
      "ordinal": 2238,
      "style": "BodyCJK",
      "text": "触发点把前瞻连接到复核：观察到信号后，不是自动行动，而是重新评估对象、路径、概率、规范和授权。高风险情形还应设置否决触发点，例如保护底板被突破、关键受影响者无法退出、数据来源失真或模型校准恶化。"
    },
    {
      "anchor": "V82-P2239",
      "ordinal": 2239,
      "style": "SecH2",
      "text": "12.7　前瞻的失败语义"
    },
    {
      "anchor": "V82-P2240",
      "ordinal": 2240,
      "style": "BodyCJK",
      "text": "到期后结果可以是支持、未支持、未决、目标失效或无法评价。未决不是成功与失败的折中，而是合同规定的证据不足状态；无法评价必须说明数据、对象、期限或执行出了什么问题。目标失效表示预测对象或同一性判据已转换，不能把它计为命中。"
    },
    {
      "anchor": "V82-P2241",
      "ordinal": 2241,
      "style": "BodyCJK",
      "text": "结果后改目标、改期限、改圈层范围或把多个路径合并成“某种程度发生”，都不能保留原前瞻的成功资格。新解释可以建立新版本，但旧记录继续存在。"
    },
    {
      "anchor": "V82-P2242",
      "ordinal": 2242,
      "style": "SecH2",
      "text": "12.8　从前瞻到有限选择的桥"
    },
    {
      "anchor": "V82-P2243",
      "ordinal": 2243,
      "style": "BodyCJK",
      "text": "前瞻输出只回答条件后果。进入有限选择前，必须补入：明示规范前提、选择主体、管辖权、受影响位置、权利底线、方案、成本与收益分布、授权、停止、申诉、回滚和补救。这里继续调用 N、PF、J、O 与 C12，不建立预测捷径。"
    },
    {
      "anchor": "V82-P2244",
      "ordinal": 2244,
      "style": "BodyCJK",
      "text": "预测不能自动生成授权。即使某条路径概率极高，也不说明任何人有权强迫他人承担避免该路径的成本；即使某行动平均收益最大，也不说明少数位置的权利可以被忽略；即使模型推荐不行动，也要审查不行动造成的持续伤害和责任。"
    },
    {
      "anchor": "V82-P2245",
      "ordinal": 2245,
      "style": "SecH2",
      "text": "12.9　方案集必须包含行动与不行动"
    },
    {
      "anchor": "V82-P2246",
      "ordinal": 2246,
      "style": "BodyCJK",
      "text": "最低方案集包括维持现状、主动行动、延迟行动、试探性小步行动、退出或转移，以及明确的不行动。具体任务可以增加方案，但不能删除不行动，也不能把维持现状和不行动混为一项：维持现状可能需要持续资源和执行，不行动可能让现状自然变化。"
    },
    {
      "anchor": "V82-P2247",
      "ordinal": 2247,
      "style": "TableHead",
      "text": "方案类型"
    },
    {
      "anchor": "V82-P2248",
      "ordinal": 2248,
      "style": "TableHead",
      "text": "主要用途"
    },
    {
      "anchor": "V82-P2249",
      "ordinal": 2249,
      "style": "TableHead",
      "text": "必须检查的风险"
    },
    {
      "anchor": "V82-P2250",
      "ordinal": 2250,
      "style": "TableText",
      "text": "维持现状"
    },
    {
      "anchor": "V82-P2251",
      "ordinal": 2251,
      "style": "TableText",
      "text": "保护已有稳定与承接"
    },
    {
      "anchor": "V82-P2252",
      "ordinal": 2252,
      "style": "TableText",
      "text": "隐性成本、持续伤害、锁定"
    },
    {
      "anchor": "V82-P2253",
      "ordinal": 2253,
      "style": "TableText",
      "text": "主动行动"
    },
    {
      "anchor": "V82-P2254",
      "ordinal": 2254,
      "style": "TableText",
      "text": "快速改变路径或条件"
    },
    {
      "anchor": "V82-P2255",
      "ordinal": 2255,
      "style": "TableText",
      "text": "权限、不可逆、跨圈层溢出"
    },
    {
      "anchor": "V82-P2256",
      "ordinal": 2256,
      "style": "TableText",
      "text": "延迟行动"
    },
    {
      "anchor": "V82-P2257",
      "ordinal": 2257,
      "style": "TableText",
      "text": "等待信息、程序或时机"
    },
    {
      "anchor": "V82-P2258",
      "ordinal": 2258,
      "style": "TableText",
      "text": "延迟本身的损害和机会损失"
    },
    {
      "anchor": "V82-P2259",
      "ordinal": 2259,
      "style": "TableText",
      "text": "试探行动"
    },
    {
      "anchor": "V82-P2260",
      "ordinal": 2260,
      "style": "TableText",
      "text": "以可逆小步获取信息"
    },
    {
      "anchor": "V82-P2261",
      "ordinal": 2261,
      "style": "TableText",
      "text": "试验成本由谁承担、能否真正回滚"
    },
    {
      "anchor": "V82-P2262",
      "ordinal": 2262,
      "style": "TableText",
      "text": "退出或转移"
    },
    {
      "anchor": "V82-P2263",
      "ordinal": 2263,
      "style": "TableText",
      "text": "结束不合适的对象或关系"
    },
    {
      "anchor": "V82-P2264",
      "ordinal": 2264,
      "style": "TableText",
      "text": "无法退出者、责任与历史保存"
    },
    {
      "anchor": "V82-P2265",
      "ordinal": 2265,
      "style": "TableText",
      "text": "不行动"
    },
    {
      "anchor": "V82-P2266",
      "ordinal": 2266,
      "style": "TableText",
      "text": "避免越权或高风险动作"
    },
    {
      "anchor": "V82-P2267",
      "ordinal": 2267,
      "style": "TableText",
      "text": "默认偏向、持续后果和不作为责任"
    },
    {
      "anchor": "V82-P2268",
      "ordinal": 2268,
      "style": "BodyCJK",
      "text": "“不行动”不是不发生任何事。其他行动者、圈层、资源和时钟仍在变化。不行动方案要有基线时点、预期路径、观察计划、重新开启条件和责任主体。"
    },
    {
      "anchor": "V82-P2269",
      "ordinal": 2269,
      "style": "SecH2",
      "text": "12.10　统一方案比较卡"
    },
    {
      "anchor": "V82-P2270",
      "ordinal": 2270,
      "style": "BodyCJK",
      "text": "每个方案使用同一基线比较，至少登记：方案描述、前瞻引用、规范前提、受影响者、权利底线、预期路径、最坏可接受结果、跨圈层溢出、成本与收益分布、信息价值、锁定风险、可逆性、资源成本、执行者、授权、停止、回滚和补救。"
    },
    {
      "anchor": "V82-P2271",
      "ordinal": 2271,
      "style": "TableHead",
      "text": "比较维度"
    },
    {
      "anchor": "V82-P2272",
      "ordinal": 2272,
      "style": "TableHead",
      "text": "问题"
    },
    {
      "anchor": "V82-P2273",
      "ordinal": 2273,
      "style": "TableHead",
      "text": "不能用什么替代"
    },
    {
      "anchor": "V82-P2274",
      "ordinal": 2274,
      "style": "TableText",
      "text": "目标与路径"
    },
    {
      "anchor": "V82-P2275",
      "ordinal": 2275,
      "style": "TableText",
      "text": "它试图改变哪条路径"
    },
    {
      "anchor": "V82-P2276",
      "ordinal": 2276,
      "style": "TableText",
      "text": "抽象的“变好”"
    },
    {
      "anchor": "V82-P2277",
      "ordinal": 2277,
      "style": "TableText",
      "text": "保护底板"
    },
    {
      "anchor": "V82-P2278",
      "ordinal": 2278,
      "style": "TableText",
      "text": "谁可能受到不可接受损害"
    },
    {
      "anchor": "V82-P2279",
      "ordinal": 2279,
      "style": "TableText",
      "text": "平均收益"
    },
    {
      "anchor": "V82-P2280",
      "ordinal": 2280,
      "style": "TableText",
      "text": "分配"
    },
    {
      "anchor": "V82-P2281",
      "ordinal": 2281,
      "style": "TableText",
      "text": "谁获益、谁付出、何时发生"
    },
    {
      "anchor": "V82-P2282",
      "ordinal": 2282,
      "style": "TableText",
      "text": "总量净值"
    },
    {
      "anchor": "V82-P2283",
      "ordinal": 2283,
      "style": "TableText",
      "text": "跨圈层溢出"
    },
    {
      "anchor": "V82-P2284",
      "ordinal": 2284,
      "style": "TableText",
      "text": "局部改善是否外部化成本"
    },
    {
      "anchor": "V82-P2285",
      "ordinal": 2285,
      "style": "TableText",
      "text": "主圈层指标"
    },
    {
      "anchor": "V82-P2286",
      "ordinal": 2286,
      "style": "TableText",
      "text": "信息价值"
    },
    {
      "anchor": "V82-P2287",
      "ordinal": 2287,
      "style": "TableText",
      "text": "是否能区分机制或路径"
    },
    {
      "anchor": "V82-P2288",
      "ordinal": 2288,
      "style": "TableText",
      "text": "行动本身的戏剧性"
    },
    {
      "anchor": "V82-P2289",
      "ordinal": 2289,
      "style": "TableText",
      "text": "可逆与锁定"
    },
    {
      "anchor": "V82-P2290",
      "ordinal": 2290,
      "style": "TableText",
      "text": "错了能否停、退、补救"
    },
    {
      "anchor": "V82-P2291",
      "ordinal": 2291,
      "style": "TableText",
      "text": "口头承诺"
    },
    {
      "anchor": "V82-P2292",
      "ordinal": 2292,
      "style": "TableText",
      "text": "权限"
    },
    {
      "anchor": "V82-P2293",
      "ordinal": 2293,
      "style": "TableText",
      "text": "谁可以决定、执行和申诉"
    },
    {
      "anchor": "V82-P2294",
      "ordinal": 2294,
      "style": "TableText",
      "text": "模型建议或职位名称"
    },
    {
      "anchor": "V82-P2295",
      "ordinal": 2295,
      "style": "TableText",
      "text": "不行动"
    },
    {
      "anchor": "V82-P2296",
      "ordinal": 2296,
      "style": "TableText",
      "text": "不做会沿什么路径变化"
    },
    {
      "anchor": "V82-P2297",
      "ordinal": 2297,
      "style": "TableText",
      "text": "假定零成本"
    },
    {
      "anchor": "V82-P2298",
      "ordinal": 2298,
      "style": "BodyCJK",
      "text": "若方案之间无法用单一尺度比较，应保留多维结果和公开冲突，而不是强行求和。若价值前提之间冲突，应由有资格的主体和程序处理，模型只能显示冲突位置与后果。"
    },
    {
      "anchor": "V82-P2299",
      "ordinal": 2299,
      "style": "SecH2",
      "text": "12.11　行动上限与信息性试验"
    },
    {
      "anchor": "V82-P2300",
      "ordinal": 2300,
      "style": "BodyCJK",
      "text": "证据、可逆性、权限和保护共同决定行动上限。证据弱、风险高、不可逆或权限不足时，合适输出可能是先观察、缩小动作、改善信息、保护受影响者、启动申诉或当前不行动。"
    },
    {
      "anchor": "V82-P2301",
      "ordinal": 2301,
      "style": "BodyCJK",
      "text": "信息性试验不是免责任的“小动作”。它仍需说明试验对象、受影响者、最小范围、可逆性、停止、数据用途和补救。不能把低权力位置当作模型校准材料，也不能在没有真实退出能力时宣称自愿参与。"
    },
    {
      "anchor": "V82-P2302",
      "ordinal": 2302,
      "style": "TableHead",
      "text": "条件组合"
    },
    {
      "anchor": "V82-P2303",
      "ordinal": 2303,
      "style": "TableHead",
      "text": "允许上限示例"
    },
    {
      "anchor": "V82-P2304",
      "ordinal": 2304,
      "style": "TableText",
      "text": "证据弱、损害低、可逆、授权清楚"
    },
    {
      "anchor": "V82-P2305",
      "ordinal": 2305,
      "style": "TableText",
      "text": "小范围观察或试探行动"
    },
    {
      "anchor": "V82-P2306",
      "ordinal": 2306,
      "style": "TableText",
      "text": "证据中等、损害可控、可回滚"
    },
    {
      "anchor": "V82-P2307",
      "ordinal": 2307,
      "style": "TableText",
      "text": "分阶段行动并设强停止门"
    },
    {
      "anchor": "V82-P2308",
      "ordinal": 2308,
      "style": "TableText",
      "text": "证据强但权限不足"
    },
    {
      "anchor": "V82-P2309",
      "ordinal": 2309,
      "style": "TableText",
      "text": "提交有权限主体，不自行执行"
    },
    {
      "anchor": "V82-P2310",
      "ordinal": 2310,
      "style": "TableText",
      "text": "证据强但不可逆且保护未满足"
    },
    {
      "anchor": "V82-P2311",
      "ordinal": 2311,
      "style": "TableText",
      "text": "暂停，补足程序与保护"
    },
    {
      "anchor": "V82-P2312",
      "ordinal": 2312,
      "style": "TableText",
      "text": "紧急安全威胁"
    },
    {
      "anchor": "V82-P2313",
      "ordinal": 2313,
      "style": "TableText",
      "text": "仅按外部紧急授权做最小保护动作，并尽快复核"
    },
    {
      "anchor": "V82-P2314",
      "ordinal": 2314,
      "style": "SecH2",
      "text": "12.12　结果回写与模型学习"
    },
    {
      "anchor": "V82-P2315",
      "ordinal": 2315,
      "style": "BodyCJK",
      "text": "前瞻和选择的结果回写只能追加。记录包括结果观察时间、来源、实际结果、路径匹配、校准指标、简单基线比较、意外效应、受影响位置复核、模型更新、断言降级、退役变量或路径和下一次复核。"
    },
    {
      "anchor": "V82-P2316",
      "ordinal": 2316,
      "style": "BodyCJK",
      "text": "行动结果不能只按主目标评价。还要检查副作用、跨圈层溢出、成本分配、申诉、无法退出者和长期时钟。一次成功不证明机制普遍成立，一次失败也可能来自执行偏离；两者要通过冻结合同区分，不能用执行解释随意救援模型。"
    },
    {
      "anchor": "V82-P2317",
      "ordinal": 2317,
      "style": "SecH2",
      "text": "12.13　一个完整的前瞻—选择示例"
    },
    {
      "anchor": "V82-P2318",
      "ordinal": 2318,
      "style": "BodyCJK",
      "text": "继续公开离职事件。条件前瞻可以把目标设为“未来三个月团队自愿离职是否明显高于历史与同类团队基线”，输入截止为公开说明后一周。简单基线使用历史离职率和工时趋势；多圈层模型增加团队信任、管理回应、职业社群桥接、家庭照护与平台曝光。路径包括舆论消退而内部持续、制度调整并逐步修复、外部桥接触发连续退出等。"
    },
    {
      "anchor": "V82-P2319",
      "ordinal": 2319,
      "style": "BodyCJK",
      "text": "早期信号包括工时实际变化、申诉处理、成员表达、招聘与外部机会；反向信号包括政策发布但执行缺失、公开安静而内部沉默增加。三个月后比较多圈层模型与简单基线，不能只挑中间某个命中信号宣布成功。"
    },
    {
      "anchor": "V82-P2320",
      "ordinal": 2320,
      "style": "BodyCJK",
      "text": "有限选择至少比较：维持现状；只做公关回应；立即资源调整；先做可逆的工时与申诉试点；延迟重大重组以收集信息；允许团队成员转移；当前不做结构行动但加强保护与观察。每项都要检查权限、无法退出者、成本分配、跨圈层声誉与家庭影响、停止和补救。模型可以显示哪些方案在哪些条件下更可能改变路径，但最终选择仍取决于规范前提、合法授权和受影响者程序。"
    },
    {
      "anchor": "V82-P2321",
      "ordinal": 2321,
      "style": "SecH2",
      "text": "12.14　何时选择不做"
    },
    {
      "anchor": "V82-P2322",
      "ordinal": 2322,
      "style": "BodyCJK",
      "text": "不做可能是谨慎，也可能是逃避。以下情形支持当前不行动或只做保护性观察：对象与事实尚不清楚；行动不可逆而证据不足；权限缺失；保护底板未满足；预计行动会把成本转嫁给无法退出者；简单基线与复杂模型均无法区分路径；现有恢复过程可能被外部干预打断。"
    },
    {
      "anchor": "V82-P2323",
      "ordinal": 2323,
      "style": "BodyCJK",
      "text": "以下情形使不行动必须接受更严格审查：持续伤害正在发生；不作为强化既得优势；负责主体有明确法定义务或承诺；低权力位置无法自行退出；延迟会造成不可逆锁定；以“等待更多证据”为由无限推迟。此时即使不采取主行动，也可能需要最小保护、信息公开、申诉通道或临时承接。"
    },
    {
      "anchor": "V82-P2324",
      "ordinal": 2324,
      "style": "SecH2",
      "text": "12.15　本部分的停止位置"
    },
    {
      "anchor": "V82-P2325",
      "ordinal": 2325,
      "style": "BodyCJK",
      "text": "条件前瞻层可以发布有目标、有期限、有基线、有信号、有校准和有回写的判断。有限选择层可以在规范、保护与授权都明确时比较行动、延迟、试探、退出和不行动，并给出条件化、可撤回的选择记录。"
    },
    {
      "anchor": "V82-P2326",
      "ordinal": 2326,
      "style": "BodyCJK",
      "text": "它们不能保证未来，不能消除价值冲突，不能替代法律、专业规范、受影响者参与和现实授权，也不能把模型准确率兑换成统治资格。任何越过这些边界的调用都应由第十三部分的工具闸阻止，并由第十六部分治理、暂停或退役。"
    },
    {
      "anchor": "V82-P2327",
      "ordinal": 2327,
      "style": "SecH2",
      "text": "12.16　面向读者的发布格式"
    },
    {
      "anchor": "V82-P2328",
      "ordinal": 2328,
      "style": "BodyCJK",
      "text": "对外发布时，前瞻摘要应先写条件，后写判断，再写不确定和更新点。推荐次序是：当前截止时点；目标与期限；对象和圈层范围；简单基线；最受支持的两至三条路径；每条路径成立所需条件；早期与反向信号；当前表达强度；暂停和下一次复核。不得把条件藏在脚注，把最强结论放在标题，也不得用“模型认为”替代证据责任。"
    },
    {
      "anchor": "V82-P2329",
      "ordinal": 2329,
      "style": "BodyCJK",
      "text": "有限选择摘要应另起一栏，明确它已经进入规范层。依次列出价值前提、决定主体、受影响位置、保护底板、可选方案、行动与不行动的分配后果、授权状态、行动上限、停止、回滚和补救。若授权尚未通过，摘要只能写“需要满足的条件”，不能用祈使语气伪装成可执行决定。"
    },
    {
      "anchor": "V82-P2330",
      "ordinal": 2330,
      "style": "TableHead",
      "text": "发布状态"
    },
    {
      "anchor": "V82-P2331",
      "ordinal": 2331,
      "style": "TableHead",
      "text": "可使用的表述"
    },
    {
      "anchor": "V82-P2332",
      "ordinal": 2332,
      "style": "TableHead",
      "text": "必须避免"
    },
    {
      "anchor": "V82-P2333",
      "ordinal": 2333,
      "style": "TableText",
      "text": "仅解释"
    },
    {
      "anchor": "V82-P2334",
      "ordinal": 2334,
      "style": "TableText",
      "text": "“现有证据支持机制 A，并保留 B”"
    },
    {
      "anchor": "V82-P2335",
      "ordinal": 2335,
      "style": "TableText",
      "text": "“因此下一步必然发生”"
    },
    {
      "anchor": "V82-P2336",
      "ordinal": 2336,
      "style": "TableText",
      "text": "仅推演"
    },
    {
      "anchor": "V82-P2337",
      "ordinal": 2337,
      "style": "TableText",
      "text": "“若 X 持续且 Y 发生，路径 P 获得支持”"
    },
    {
      "anchor": "V82-P2338",
      "ordinal": 2338,
      "style": "TableText",
      "text": "“模型预测 P 已经确定”"
    },
    {
      "anchor": "V82-P2339",
      "ordinal": 2339,
      "style": "TableText",
      "text": "已登记前瞻"
    },
    {
      "anchor": "V82-P2340",
      "ordinal": 2340,
      "style": "TableText",
      "text": "“在期限 T 内，P 当前优先于 Q，见反向信号 S”"
    },
    {
      "anchor": "V82-P2341",
      "ordinal": 2341,
      "style": "TableText",
      "text": "隐去基线、期限和失败条件"
    },
    {
      "anchor": "V82-P2342",
      "ordinal": 2342,
      "style": "TableText",
      "text": "规范尚未通过"
    },
    {
      "anchor": "V82-P2343",
      "ordinal": 2343,
      "style": "TableText",
      "text": "“若要行动，仍需 N、PF、J 与 O”"
    },
    {
      "anchor": "V82-P2344",
      "ordinal": 2344,
      "style": "TableText",
      "text": "“建议立即执行”"
    },
    {
      "anchor": "V82-P2345",
      "ordinal": 2345,
      "style": "TableText",
      "text": "已获外部授权"
    },
    {
      "anchor": "V82-P2346",
      "ordinal": 2346,
      "style": "TableText",
      "text": "“授权记录允许主体在上限内执行并按条件停止”"
    },
    {
      "anchor": "V82-P2347",
      "ordinal": 2347,
      "style": "TableText",
      "text": "把授权归因于模型"
    },
    {
      "anchor": "V82-P2348",
      "ordinal": 2348,
      "style": "BodyCJK",
      "text": "发布后的解释权也受治理。读者误把条件前瞻当确定预言、把人格候选当事实或把方案比较当命令时，发布者应更正，而不是利用误读扩大影响。任何更新都以新版本追加，原标题、概率、期限与失败记录保持可追踪。"
    }
  ],
  "tables": [
    {
      "anchor": "V82-T048",
      "cell_paragraph_ordinals": [
        [
          [
            2136
          ],
          [
            2137
          ],
          [
            2138
          ],
          [
            2139
          ]
        ],
        [
          [
            2140
          ],
          [
            2141
          ],
          [
            2142
          ],
          [
            2143
          ]
        ],
        [
          [
            2144
          ],
          [
            2145
          ],
          [
            2146
          ],
          [
            2147
          ]
        ],
        [
          [
            2148
          ],
          [
            2149
          ],
          [
            2150
          ],
          [
            2151
          ]
        ],
        [
          [
            2152
          ],
          [
            2153
          ],
          [
            2154
          ],
          [
            2155
          ]
        ]
      ],
      "ordinal": 48,
      "paragraph_ordinals": [
        2136,
        2137,
        2138,
        2139,
        2140,
        2141,
        2142,
        2143,
        2144,
        2145,
        2146,
        2147,
        2148,
        2149,
        2150,
        2151,
        2152,
        2153,
        2154,
        2155
      ],
      "rows": [
        [
          "输出",
          "核心问题",
          "必需输入",
          "输出上限"
        ],
        [
          "解释",
          "已发生什么，可能为何发生",
          "对象、尺度、证据、机制、反例",
          "有边界的机制说明"
        ],
        [
          "推演",
          "条件或事件后可能沿哪些路径演化",
          "冻结快照、更新规则、时钟、分叉",
          "条件路径和区分信号"
        ],
        [
          "条件前瞻",
          "在目标与期限内哪条路径更值得期待",
          "结果前登记、简单基线、指标、回写",
          "可校准、可失败的判断"
        ],
        [
          "有限选择",
          "在规范和授权下可做、如何做或不做",
          "前瞻、N、PF、J、O、C12、方案与受影响者",
          "有条件、可撤回的选择记录"
        ]
      ]
    },
    {
      "anchor": "V82-T049",
      "cell_paragraph_ordinals": [
        [
          [
            2160
          ],
          [
            2161
          ],
          [
            2162
          ]
        ],
        [
          [
            2163
          ],
          [
            2164
          ],
          [
            2165
          ]
        ],
        [
          [
            2166
          ],
          [
            2167
          ],
          [
            2168
          ]
        ],
        [
          [
            2169
          ],
          [
            2170
          ],
          [
            2171
          ]
        ],
        [
          [
            2172
          ],
          [
            2173
          ],
          [
            2174
          ]
        ],
        [
          [
            2175
          ],
          [
            2176
          ],
          [
            2177
          ]
        ],
        [
          [
            2178
          ],
          [
            2179
          ],
          [
            2180
          ]
        ],
        [
          [
            2181
          ],
          [
            2182
          ],
          [
            2183
          ]
        ]
      ],
      "ordinal": 49,
      "paragraph_ordinals": [
        2160,
        2161,
        2162,
        2163,
        2164,
        2165,
        2166,
        2167,
        2168,
        2169,
        2170,
        2171,
        2172,
        2173,
        2174,
        2175,
        2176,
        2177,
        2178,
        2179,
        2180,
        2181,
        2182,
        2183
      ],
      "rows": [
        [
          "登记项",
          "最低问题",
          "防止的偏差"
        ],
        [
          "目标",
          "到期时如何知道发生、未发生或无法判断",
          "模糊成功"
        ],
        [
          "期限",
          "从何时到何时，何时停止收集输入",
          "无限等待"
        ],
        [
          "简单基线",
          "不用多圈层机制时的比较预测是什么",
          "复杂故事自我胜利"
        ],
        [
          "路径",
          "哪些路径互斥、并行或不可比较",
          "事后挑选"
        ],
        [
          "表达",
          "概率、区间、等级还是仅方向",
          "伪精确"
        ],
        [
          "信号",
          "什么提高或降低路径支持",
          "只找支持证据"
        ],
        [
          "回写",
          "结果由何来源、何时追加",
          "失败消失"
        ]
      ]
    },
    {
      "anchor": "V82-T050",
      "cell_paragraph_ordinals": [
        [
          [
            2196
          ],
          [
            2197
          ],
          [
            2198
          ]
        ],
        [
          [
            2199
          ],
          [
            2200
          ],
          [
            2201
          ]
        ],
        [
          [
            2202
          ],
          [
            2203
          ],
          [
            2204
          ]
        ],
        [
          [
            2205
          ],
          [
            2206
          ],
          [
            2207
          ]
        ],
        [
          [
            2208
          ],
          [
            2209
          ],
          [
            2210
          ]
        ]
      ],
      "ordinal": 50,
      "paragraph_ordinals": [
        2196,
        2197,
        2198,
        2199,
        2200,
        2201,
        2202,
        2203,
        2204,
        2205,
        2206,
        2207,
        2208,
        2209,
        2210
      ],
      "rows": [
        [
          "证据状态",
          "合适表达",
          "必须同时给出"
        ],
        [
          "有充分历史样本和稳定目标",
          "概率或概率区间",
          "校准、分辨率、基线和置信区间"
        ],
        [
          "样本有限但路径可区分",
          "支持等级或排序",
          "依据、不可比较项和反向信号"
        ],
        [
          "机制候选多、数据稀疏",
          "条件方向",
          "触发点、最小观察和停止条件"
        ],
        [
          "目标或对象不稳定",
          "不发布前瞻",
          "需要重新定义的合同"
        ]
      ]
    },
    {
      "anchor": "V82-T051",
      "cell_paragraph_ordinals": [
        [
          [
            2215
          ],
          [
            2216
          ],
          [
            2217
          ]
        ],
        [
          [
            2218
          ],
          [
            2219
          ],
          [
            2220
          ]
        ],
        [
          [
            2221
          ],
          [
            2222
          ],
          [
            2223
          ]
        ],
        [
          [
            2224
          ],
          [
            2225
          ],
          [
            2226
          ]
        ],
        [
          [
            2227
          ],
          [
            2228
          ],
          [
            2229
          ]
        ],
        [
          [
            2230
          ],
          [
            2231
          ],
          [
            2232
          ]
        ],
        [
          [
            2233
          ],
          [
            2234
          ],
          [
            2235
          ]
        ]
      ],
      "ordinal": 51,
      "paragraph_ordinals": [
        2215,
        2216,
        2217,
        2218,
        2219,
        2220,
        2221,
        2222,
        2223,
        2224,
        2225,
        2226,
        2227,
        2228,
        2229,
        2230,
        2231,
        2232,
        2233,
        2234,
        2235
      ],
      "rows": [
        [
          "评价维度",
          "说明",
          "失败后的动作"
        ],
        [
          "校准",
          "说 70% 的事件长期是否约 70% 发生",
          "调整表达或降级概率输出"
        ],
        [
          "分辨率",
          "模型能否区分不同风险或路径",
          "删除无贡献变量、退回基线"
        ],
        [
          "覆盖率",
          "区间或时间窗是否覆盖实际结果",
          "扩大区间或修正时钟"
        ],
        [
          "基线增益",
          "是否优于简单模型",
          "停止复杂模型的前瞻声明"
        ],
        [
          "稳定性",
          "跨时间、地点和边界是否保持",
          "限定适用域或退役"
        ],
        [
          "分配误差",
          "哪些位置持续被低估或误报",
          "受影响者复核、补救和保护升级"
        ]
      ]
    },
    {
      "anchor": "V82-T052",
      "cell_paragraph_ordinals": [
        [
          [
            2247
          ],
          [
            2248
          ],
          [
            2249
          ]
        ],
        [
          [
            2250
          ],
          [
            2251
          ],
          [
            2252
          ]
        ],
        [
          [
            2253
          ],
          [
            2254
          ],
          [
            2255
          ]
        ],
        [
          [
            2256
          ],
          [
            2257
          ],
          [
            2258
          ]
        ],
        [
          [
            2259
          ],
          [
            2260
          ],
          [
            2261
          ]
        ],
        [
          [
            2262
          ],
          [
            2263
          ],
          [
            2264
          ]
        ],
        [
          [
            2265
          ],
          [
            2266
          ],
          [
            2267
          ]
        ]
      ],
      "ordinal": 52,
      "paragraph_ordinals": [
        2247,
        2248,
        2249,
        2250,
        2251,
        2252,
        2253,
        2254,
        2255,
        2256,
        2257,
        2258,
        2259,
        2260,
        2261,
        2262,
        2263,
        2264,
        2265,
        2266,
        2267
      ],
      "rows": [
        [
          "方案类型",
          "主要用途",
          "必须检查的风险"
        ],
        [
          "维持现状",
          "保护已有稳定与承接",
          "隐性成本、持续伤害、锁定"
        ],
        [
          "主动行动",
          "快速改变路径或条件",
          "权限、不可逆、跨圈层溢出"
        ],
        [
          "延迟行动",
          "等待信息、程序或时机",
          "延迟本身的损害和机会损失"
        ],
        [
          "试探行动",
          "以可逆小步获取信息",
          "试验成本由谁承担、能否真正回滚"
        ],
        [
          "退出或转移",
          "结束不合适的对象或关系",
          "无法退出者、责任与历史保存"
        ],
        [
          "不行动",
          "避免越权或高风险动作",
          "默认偏向、持续后果和不作为责任"
        ]
      ]
    },
    {
      "anchor": "V82-T053",
      "cell_paragraph_ordinals": [
        [
          [
            2271
          ],
          [
            2272
          ],
          [
            2273
          ]
        ],
        [
          [
            2274
          ],
          [
            2275
          ],
          [
            2276
          ]
        ],
        [
          [
            2277
          ],
          [
            2278
          ],
          [
            2279
          ]
        ],
        [
          [
            2280
          ],
          [
            2281
          ],
          [
            2282
          ]
        ],
        [
          [
            2283
          ],
          [
            2284
          ],
          [
            2285
          ]
        ],
        [
          [
            2286
          ],
          [
            2287
          ],
          [
            2288
          ]
        ],
        [
          [
            2289
          ],
          [
            2290
          ],
          [
            2291
          ]
        ],
        [
          [
            2292
          ],
          [
            2293
          ],
          [
            2294
          ]
        ],
        [
          [
            2295
          ],
          [
            2296
          ],
          [
            2297
          ]
        ]
      ],
      "ordinal": 53,
      "paragraph_ordinals": [
        2271,
        2272,
        2273,
        2274,
        2275,
        2276,
        2277,
        2278,
        2279,
        2280,
        2281,
        2282,
        2283,
        2284,
        2285,
        2286,
        2287,
        2288,
        2289,
        2290,
        2291,
        2292,
        2293,
        2294,
        2295,
        2296,
        2297
      ],
      "rows": [
        [
          "比较维度",
          "问题",
          "不能用什么替代"
        ],
        [
          "目标与路径",
          "它试图改变哪条路径",
          "抽象的“变好”"
        ],
        [
          "保护底板",
          "谁可能受到不可接受损害",
          "平均收益"
        ],
        [
          "分配",
          "谁获益、谁付出、何时发生",
          "总量净值"
        ],
        [
          "跨圈层溢出",
          "局部改善是否外部化成本",
          "主圈层指标"
        ],
        [
          "信息价值",
          "是否能区分机制或路径",
          "行动本身的戏剧性"
        ],
        [
          "可逆与锁定",
          "错了能否停、退、补救",
          "口头承诺"
        ],
        [
          "权限",
          "谁可以决定、执行和申诉",
          "模型建议或职位名称"
        ],
        [
          "不行动",
          "不做会沿什么路径变化",
          "假定零成本"
        ]
      ]
    },
    {
      "anchor": "V82-T054",
      "cell_paragraph_ordinals": [
        [
          [
            2302
          ],
          [
            2303
          ]
        ],
        [
          [
            2304
          ],
          [
            2305
          ]
        ],
        [
          [
            2306
          ],
          [
            2307
          ]
        ],
        [
          [
            2308
          ],
          [
            2309
          ]
        ],
        [
          [
            2310
          ],
          [
            2311
          ]
        ],
        [
          [
            2312
          ],
          [
            2313
          ]
        ]
      ],
      "ordinal": 54,
      "paragraph_ordinals": [
        2302,
        2303,
        2304,
        2305,
        2306,
        2307,
        2308,
        2309,
        2310,
        2311,
        2312,
        2313
      ],
      "rows": [
        [
          "条件组合",
          "允许上限示例"
        ],
        [
          "证据弱、损害低、可逆、授权清楚",
          "小范围观察或试探行动"
        ],
        [
          "证据中等、损害可控、可回滚",
          "分阶段行动并设强停止门"
        ],
        [
          "证据强但权限不足",
          "提交有权限主体，不自行执行"
        ],
        [
          "证据强但不可逆且保护未满足",
          "暂停，补足程序与保护"
        ],
        [
          "紧急安全威胁",
          "仅按外部紧急授权做最小保护动作，并尽快复核"
        ]
      ]
    },
    {
      "anchor": "V82-T055",
      "cell_paragraph_ordinals": [
        [
          [
            2330
          ],
          [
            2331
          ],
          [
            2332
          ]
        ],
        [
          [
            2333
          ],
          [
            2334
          ],
          [
            2335
          ]
        ],
        [
          [
            2336
          ],
          [
            2337
          ],
          [
            2338
          ]
        ],
        [
          [
            2339
          ],
          [
            2340
          ],
          [
            2341
          ]
        ],
        [
          [
            2342
          ],
          [
            2343
          ],
          [
            2344
          ]
        ],
        [
          [
            2345
          ],
          [
            2346
          ],
          [
            2347
          ]
        ]
      ],
      "ordinal": 55,
      "paragraph_ordinals": [
        2330,
        2331,
        2332,
        2333,
        2334,
        2335,
        2336,
        2337,
        2338,
        2339,
        2340,
        2341,
        2342,
        2343,
        2344,
        2345,
        2346,
        2347
      ],
      "rows": [
        [
          "发布状态",
          "可使用的表述",
          "必须避免"
        ],
        [
          "仅解释",
          "“现有证据支持机制 A，并保留 B”",
          "“因此下一步必然发生”"
        ],
        [
          "仅推演",
          "“若 X 持续且 Y 发生，路径 P 获得支持”",
          "“模型预测 P 已经确定”"
        ],
        [
          "已登记前瞻",
          "“在期限 T 内，P 当前优先于 Q，见反向信号 S”",
          "隐去基线、期限和失败条件"
        ],
        [
          "规范尚未通过",
          "“若要行动，仍需 N、PF、J 与 O”",
          "“建议立即执行”"
        ],
        [
          "已获外部授权",
          "“授权记录允许主体在上限内执行并按条件停止”",
          "把授权归因于模型"
        ]
      ]
    }
  ]
}
```
<!-- canonical-records:end -->
