# CrossFrame Ultra v8.2 第十三部分　接口与工具

Raw SHA256: `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
Source role: `division`
Paragraph range: `V82-P2349`-`V82-P2600`
Paragraph count: `252`
Tables: `V82-T056, V82-T057, V82-T058, V82-T059, V82-T060, V82-T061, V82-T062, V82-T063`

## Source Paragraphs

<!-- source-paragraph:V82-P2349 style=PartTitle -->
第十三部分　接口与工具

<!-- source-paragraph:V82-P2350 style=BodyCJK -->
本部分把此前十二部分定义的对象、命题、尺度、机制、行动者、多圈层联合状态和动态推演要求转换为可观察、可质疑、可复核、可撤回的有限判断。它不新增世界事实，也不把表格完整度当作事实成立。进入工具流前，必须已有 D0 候选对象记录和九轴尺度记录；对象、边界、尺度、时间窗、同一性判据或用途改变时，已有判断不得平移沿用。

<!-- source-paragraph:V82-P2351 style=BodyCJK -->
工具流程采用两级结构：七闸是唯一主流程，五闸十三步是诊断展开层。七闸回答判断能否进入下一层；五闸十三步在复杂案例中展开需要提交的材料，但不另行出具与七闸竞争的“通过”结论，也不产生第二套流程状态。

<!-- source-paragraph:V82-P2352 style=BodyCJK -->
最重要的边界是：工具层不产生授权。流程、证据、强判断八件套全部完成，也只产生描述、候选机制、比较判断、强判断候选或行动要求。现实行动仍须另经结构化选择记录、C12 十组件桥、同一条有效 J 原子授权以及 O1-O4；工具输出不能替代其中任何一项。

<!-- source-paragraph:V82-P2353 style=SecH2 -->
13.1　四次转换

<!-- source-paragraph:V82-P2354 style=BodyCJK -->
四次转换不是把理论词换成现实标签，而是逐次增加记录责任。任一步失败，输出停在该步之前，不能靠后一步的格式完整补救。

<!-- source-paragraph:V82-P2355 style=TableHead -->
ID

<!-- source-paragraph:V82-P2356 style=TableHead -->
转换

<!-- source-paragraph:V82-P2357 style=TableHead -->
必须得到什么

<!-- source-paragraph:V82-P2358 style=TableHead -->
失败时停在哪里

<!-- source-paragraph:V82-P2359 style=TableText -->
IT1

<!-- source-paragraph:V82-P2360 style=TableText -->
结构变量到可观察信号

<!-- source-paragraph:V82-P2361 style=TableText -->
对象、尺度、观察位置、时间窗、测量协议和缺失状态明确的信号记录

<!-- source-paragraph:V82-P2362 style=TableText -->
概念映射或材料缺口

<!-- source-paragraph:V82-P2363 style=TableText -->
IT2

<!-- source-paragraph:V82-P2364 style=TableText -->
可观察信号到证据强度

<!-- source-paragraph:V82-P2365 style=TableText -->
来源、观察、比较条件、覆盖、反例、替代解释和不确定性分开的证据记录

<!-- source-paragraph:V82-P2366 style=TableText -->
未分级材料或待检验假设

<!-- source-paragraph:V82-P2367 style=TableText -->
IT3

<!-- source-paragraph:V82-P2368 style=TableText -->
证据强度到判断等级

<!-- source-paragraph:V82-P2369 style=TableText -->
有命题合同、适用边界、反向条件、证伪条件和撤回条件的判断

<!-- source-paragraph:V82-P2370 style=TableText -->
候选解释或观察意见

<!-- source-paragraph:V82-P2371 style=TableText -->
IT4

<!-- source-paragraph:V82-P2372 style=TableText -->
判断等级到行动要求与上限

<!-- source-paragraph:V82-P2373 style=TableText -->
受影响位置、保护底板、禁止动作、停止、申诉、回滚及尚缺 N/J/O/C12 的清单

<!-- source-paragraph:V82-P2374 style=TableText -->
描述、补证或不行动要求

<!-- source-paragraph:V82-P2375 style=BodyCJK -->
IT1 防止把结构叙事当成观察事实；IT2 防止把出处、材料或表态直接当成证据；IT3 防止把相关、类比或单一机制故事升级为结论；IT4 防止从事实判断直接跳到处置。四次转换全部通过也不改变授权状态。

<!-- source-paragraph:V82-P2376 style=BodyCJK -->
任何 IT 转换失败，后续转换只能记 not_run，本次运行的输出上限立即降到描述或候选机制，不得输出 comparative_judgment、strong_judgment 或 action_requirements。后续 not_run 只是保留失败链，不能重新抬高输出上限；八件套齐全也不能补回转换链上的断口。

<!-- source-paragraph:V82-P2377 style=SecH2 -->
13.2　通用原语与人类变量接口(11+11)的调用方式

<!-- source-paragraph:V82-P2378 style=BodyCJK -->
第七部分的 HV01-HV11 是人类结构化世界的十一项接口；第三部分的 U01-U11 是通用结构原语。工具层可以在同一案例中并列调用二者，但不把编号相同、数量相同或问题相似解释为一一等价。

<!-- source-paragraph:V82-P2379 style=BodyCJK -->
调用时至少登记：通用或人类接口 ID、有效对象、九轴尺度、所选支持路由、实例证据、替代解释、缺失状态、判断上限与行动上限。H1/H4/H5 只能经各自 H-instance 进入指定路由；G1-G4 只能经结果前冻结的 G-instance 支持经验主张。接口卡能提出问题，却不能因字段填满而证明对象事实。

<!-- source-paragraph:V82-P2380 style=SecH2 -->
13.3　七闸：唯一主流程

<!-- source-paragraph:V82-P2381 style=BodyCJK -->
七闸依次运行。某一闸失败后，后续闸只能记 not_run，本次运行的输出上限同时降到描述或候选机制，不得输出比较判断、强判断或行动要求。后续 not_run 不能抬高失败闸已经压低的上限，也不能一边承认对象或证据未过闸，一边让后续程序自报通过。对象、证据版本、受影响位置或用途发生实质变化时，从最早受影响的闸重新运行。

<!-- source-paragraph:V82-P2382 style=TableHead -->
ID

<!-- source-paragraph:V82-P2383 style=TableHead -->
闸门

<!-- source-paragraph:V82-P2384 style=TableHead -->
核心问题

<!-- source-paragraph:V82-P2385 style=TableHead -->
未通过时的输出上限

<!-- source-paragraph:V82-P2386 style=TableText -->
IG1

<!-- source-paragraph:V82-P2387 style=TableText -->
有效对象闸

<!-- source-paragraph:V82-P2388 style=TableText -->
对象、边界、九轴尺度、时间窗与 K 是否支持本次判断？

<!-- source-paragraph:V82-P2389 style=TableText -->
重新界定对象、尺度未知或对象转换复核

<!-- source-paragraph:V82-P2390 style=TableText -->
IG2

<!-- source-paragraph:V82-P2391 style=TableText -->
证据追踪闸

<!-- source-paragraph:V82-P2392 style=TableText -->
来源、材料、观察、证据、反例、案例与判断是否分开可回溯？

<!-- source-paragraph:V82-P2393 style=TableText -->
材料整理、候选问题或待检验假设

<!-- source-paragraph:V82-P2394 style=TableText -->
IG3

<!-- source-paragraph:V82-P2395 style=TableText -->
受影响位置闸

<!-- source-paragraph:V82-P2396 style=TableText -->
哪些直接、间接、二阶、跨域与跨期位置会改变处境？

<!-- source-paragraph:V82-P2397 style=TableText -->
补充影响核算；暂停强判断和高影响用途

<!-- source-paragraph:V82-P2398 style=TableText -->
IG4

<!-- source-paragraph:V82-P2399 style=TableText -->
权力与反报复闸

<!-- source-paragraph:V82-P2400 style=TableText -->
低权力位置能否安全补证、反驳、拒绝、停止和申诉？

<!-- source-paragraph:V82-P2401 style=TableText -->
不得因沉默作不利推断；降低发布与判断档位

<!-- source-paragraph:V82-P2402 style=TableText -->
IG5

<!-- source-paragraph:V82-P2403 style=TableText -->
中介与反身性闸

<!-- source-paragraph:V82-P2404 style=TableText -->
指标、平台、AI、公开评价或诊断行为是否改变证据和对象？

<!-- source-paragraph:V82-P2405 style=TableText -->
高反身性未收束；改写为条件状态转移

<!-- source-paragraph:V82-P2406 style=TableText -->
IG6

<!-- source-paragraph:V82-P2407 style=TableText -->
强判断程序闸

<!-- source-paragraph:V82-P2408 style=TableText -->
高影响、公开或组织化判断是否完整提交 SJ1-SJ8？

<!-- source-paragraph:V82-P2409 style=TableText -->
内部假设、开放断言或候选机制；不得形成比较判断

<!-- source-paragraph:V82-P2410 style=TableText -->
IG7

<!-- source-paragraph:V82-P2411 style=TableText -->
行动上限闸

<!-- source-paragraph:V82-P2412 style=TableText -->
最多只能提出什么要求，哪些动作禁止，何时停止、申诉和回滚？

<!-- source-paragraph:V82-P2413 style=TableText -->
描述、证据缺口、不行动或继续审议

<!-- source-paragraph:V82-P2414 style=BodyCJK -->
七闸全过不表示结论为真，只表示相应记录门没有缺口。经验命题仍由其命题合同和实例证据判定；规范目标仍需明示 N 前提；现实行动仍需选择、C12、J 与 O 程序。特别是 IG7 只能记录外部规范层与授权层是否具备，不能由工具流自己写成“已授权”。

<!-- source-paragraph:V82-P2415 style=BodyCJK -->
IG6 有一条专门适用性规则：普通 L1/L2 输出可以把它记为 not_applicable，但必须写明为什么本次不触发强判断程序，且这不会阻断 IG7；一旦 IG6 记为 passed，同一运行记录必须绑定完整、逐项 passed 的 SJ1—SJ8。用“已检查”字符串或空理由不能代替八项结果。

<!-- source-paragraph:V82-P2416 style=SecH2 -->
13.4　五闸十三步：诊断展开层

<!-- source-paragraph:V82-P2417 style=BodyCJK -->
当对象复杂、高责任、高反身性，或七闸需要展开取证时，运行五闸十三步。五闸是展开过程的局部检查，不生成第二套主流程状态。

<!-- source-paragraph:V82-P2418 style=TableHead -->
ID

<!-- source-paragraph:V82-P2419 style=TableHead -->
展开闸

<!-- source-paragraph:V82-P2420 style=TableHead -->
必须展开的材料

<!-- source-paragraph:V82-P2421 style=TableHead -->
对应主闸

<!-- source-paragraph:V82-P2422 style=TableText -->
FG1

<!-- source-paragraph:V82-P2423 style=TableText -->
对象闸

<!-- source-paragraph:V82-P2424 style=TableText -->
对象、边界、尺度、时间窗

<!-- source-paragraph:V82-P2425 style=TableText -->
IG1

<!-- source-paragraph:V82-P2426 style=TableText -->
FG2

<!-- source-paragraph:V82-P2427 style=TableText -->
证据闸

<!-- source-paragraph:V82-P2428 style=TableText -->
信号成本、来源、权重、复核

<!-- source-paragraph:V82-P2429 style=TableText -->
IG2

<!-- source-paragraph:V82-P2430 style=TableText -->
FG3

<!-- source-paragraph:V82-P2431 style=TableText -->
尺度闸

<!-- source-paragraph:V82-P2432 style=TableText -->
九轴尺度、尺度内对象与证据、尺度变化

<!-- source-paragraph:V82-P2433 style=TableText -->
IG1、IG2

<!-- source-paragraph:V82-P2434 style=TableText -->
FG4

<!-- source-paragraph:V82-P2435 style=TableText -->
责任闸

<!-- source-paragraph:V82-P2436 style=TableText -->
权利/资源影响、反向条件、修复窗口、申诉复核

<!-- source-paragraph:V82-P2437 style=TableText -->
IG3、IG4、IG6

<!-- source-paragraph:V82-P2438 style=TableText -->
FG5

<!-- source-paragraph:V82-P2439 style=TableText -->
观测闸

<!-- source-paragraph:V82-P2440 style=TableText -->
观察前基线、观察中反应、发布后反应、递归封顶

<!-- source-paragraph:V82-P2441 style=TableText -->
IG5

<!-- source-paragraph:V82-P2442 style=BodyCJK -->
十三步按现实问题到写回的顺序形成一条可审计工作链：

<!-- source-paragraph:V82-P2443 style=TableHead -->
ID

<!-- source-paragraph:V82-P2444 style=TableHead -->
步骤

<!-- source-paragraph:V82-P2445 style=TableHead -->
最小产物

<!-- source-paragraph:V82-P2446 style=TableText -->
DS01

<!-- source-paragraph:V82-P2447 style=TableText -->
问题入口

<!-- source-paragraph:V82-P2448 style=TableText -->
不使用框架术语的现实问题、请求者和用途

<!-- source-paragraph:V82-P2449 style=TableText -->
DS02

<!-- source-paragraph:V82-P2450 style=TableText -->
对象与边界

<!-- source-paragraph:V82-P2451 style=TableText -->
有效对象、子系统、上级环境和外部通道

<!-- source-paragraph:V82-P2452 style=TableText -->
DS03

<!-- source-paragraph:V82-P2453 style=TableText -->
信号分层

<!-- source-paragraph:V82-P2454 style=TableText -->
事实、行为、资源、反馈、叙事、感受、推测和噪声分栏

<!-- source-paragraph:V82-P2455 style=TableText -->
DS04

<!-- source-paragraph:V82-P2456 style=TableText -->
观测参与登记

<!-- source-paragraph:V82-P2457 style=TableText -->
被观察知情、观察者权力、发布影响和候选反应

<!-- source-paragraph:V82-P2458 style=TableText -->
DS05

<!-- source-paragraph:V82-P2459 style=TableText -->
主导约束

<!-- source-paragraph:V82-P2460 style=TableText -->
候选约束、所选约束、选择证据和竞争约束

<!-- source-paragraph:V82-P2461 style=TableText -->
DS06

<!-- source-paragraph:V82-P2462 style=TableText -->
状态与窗口

<!-- source-paragraph:V82-P2463 style=TableText -->
S0-S6 原型引用、状态内位置、并行子系统和反向条件

<!-- source-paragraph:V82-P2464 style=TableText -->
DS07

<!-- source-paragraph:V82-P2465 style=TableText -->
核心结构扫描

<!-- source-paragraph:V82-P2466 style=TableText -->
锚点、承接层、传导链、边界和反馈写回

<!-- source-paragraph:V82-P2467 style=TableText -->
DS08

<!-- source-paragraph:V82-P2468 style=TableText -->
关键保护变量

<!-- source-paragraph:V82-P2469 style=TableText -->
受保护变量、受损路径、资源、冗余和修复/回流路径

<!-- source-paragraph:V82-P2470 style=TableText -->
DS09

<!-- source-paragraph:V82-P2471 style=TableText -->
承接与偿付

<!-- source-paragraph:V82-P2472 style=TableText -->
成本承担者、回流获得者、停止权、长期透支与损害转移

<!-- source-paragraph:V82-P2473 style=TableText -->
DS10

<!-- source-paragraph:V82-P2474 style=TableText -->
隐患与边界类型

<!-- source-paragraph:V82-P2475 style=TableText -->
维护债、快慢错配、指标替代、摘要失真和对象转换候选

<!-- source-paragraph:V82-P2476 style=TableText -->
DS11

<!-- source-paragraph:V82-P2477 style=TableText -->
机制候选

<!-- source-paragraph:V82-P2478 style=TableText -->
至少两个竞争机制、各自所需证据、削弱证据和淘汰规则

<!-- source-paragraph:V82-P2479 style=TableText -->
DS12

<!-- source-paragraph:V82-P2480 style=TableText -->
分支预判

<!-- source-paragraph:V82-P2481 style=TableText -->
触发、早期信号、反向条件、修复窗口和最低行动要求

<!-- source-paragraph:V82-P2482 style=TableText -->
DS13

<!-- source-paragraph:V82-P2483 style=TableText -->
输出与写回

<!-- source-paragraph:V82-P2484 style=TableText -->
现实语言输出、修改触发器、记录范围、复核、撤回和回滚

<!-- source-paragraph:V82-P2485 style=BodyCJK -->
DS06 只能引用人类状态原型，不能把 S0-S6 写成成熟度或命运。DS08 发现重要保护变量，只能生成保护需求；DS09 发现承接或透支，不能生成牺牲义务或完整责任；DS11 的机制候选不得跨过因果合同；DS12 的分支不是确定未来；DS13 没有复核和撤回时，不得把判断写入组织记录、资格、分配或公共记忆。

<!-- source-paragraph:V82-P2486 style=SecH2 -->
13.5　强判断八件套

<!-- source-paragraph:V82-P2487 style=BodyCJK -->
强判断是可能影响处置、资格、声誉、资源、权利、公共记忆，或将被公开、自动化、组织化、制度化使用的判断。只有 L3 且七闸全过、下列八项逐项通过时，才可登记“强判断候选”；它仍不是现实行动授权。

<!-- source-paragraph:V82-P2488 style=TableHead -->
ID

<!-- source-paragraph:V82-P2489 style=TableHead -->
组件

<!-- source-paragraph:V82-P2490 style=TableHead -->
必须回答什么

<!-- source-paragraph:V82-P2491 style=TableText -->
SJ1

<!-- source-paragraph:V82-P2492 style=TableText -->
反向条件

<!-- source-paragraph:V82-P2493 style=TableText -->
出现什么情况会削弱、反转或撤回判断？

<!-- source-paragraph:V82-P2494 style=TableText -->
SJ2

<!-- source-paragraph:V82-P2495 style=TableText -->
修复窗口

<!-- source-paragraph:V82-P2496 style=TableText -->
窗口何在、根据何在、何时失效？

<!-- source-paragraph:V82-P2497 style=TableText -->
SJ3

<!-- source-paragraph:V82-P2498 style=TableText -->
证据要求

<!-- source-paragraph:V82-P2499 style=TableText -->
支持、缺失和反向证据分别是什么？

<!-- source-paragraph:V82-P2500 style=TableText -->
SJ4

<!-- source-paragraph:V82-P2501 style=TableText -->
申诉入口

<!-- source-paragraph:V82-P2502 style=TableText -->
谁可进入、谁负责、时限多长、能否改变结果？

<!-- source-paragraph:V82-P2503 style=TableText -->
SJ5

<!-- source-paragraph:V82-P2504 style=TableText -->
反报复保护

<!-- source-paragraph:V82-P2505 style=TableText -->
哪些行为受保护、如何监测、如何独立报告和补救？

<!-- source-paragraph:V82-P2506 style=TableText -->
SJ6

<!-- source-paragraph:V82-P2507 style=TableText -->
证据补充权

<!-- source-paragraph:V82-P2508 style=TableText -->
如何补证、纠正版本并同步下游？

<!-- source-paragraph:V82-P2509 style=TableText -->
SJ7

<!-- source-paragraph:V82-P2510 style=TableText -->
外部复核触发

<!-- source-paragraph:V82-P2511 style=TableText -->
何时触发、谁独立复核、能否访问材料和停止结果？

<!-- source-paragraph:V82-P2512 style=TableText -->
SJ8

<!-- source-paragraph:V82-P2513 style=TableText -->
回滚与写回

<!-- source-paragraph:V82-P2514 style=TableText -->
回到哪个状态、谁修复、哪个版本权威、如何同步？

<!-- source-paragraph:V82-P2515 style=BodyCJK -->
任何一项缺失，IG6 失败，输出降为内部假设、开放断言或候选机制，不得保留 L2 比较判断。申诉入口若不能改变记录或行动，不算有效申诉；外部名义不等于独立；声明、道歉或新版本发布不等于实际回滚和修复。

<!-- source-paragraph:V82-P2516 style=SecH2 -->
13.6　诊断档位

<!-- source-paragraph:V82-P2517 style=TableHead -->
ID

<!-- source-paragraph:V82-P2518 style=TableHead -->
档位

<!-- source-paragraph:V82-P2519 style=TableHead -->
适用

<!-- source-paragraph:V82-P2520 style=TableHead -->
输出上限

<!-- source-paragraph:V82-P2521 style=TableText -->
L1

<!-- source-paragraph:V82-P2522 style=TableText -->
轻量描述与试探问题

<!-- source-paragraph:V82-P2523 style=TableText -->
低复杂、低影响、可逆且信息有限

<!-- source-paragraph:V82-P2524 style=TableText -->
描述、问题和下一观察

<!-- source-paragraph:V82-P2525 style=TableText -->
L2

<!-- source-paragraph:V82-P2526 style=TableText -->
标准可复核判断

<!-- source-paragraph:V82-P2527 style=TableText -->
需要结构比较但不进入高责任处置

<!-- source-paragraph:V82-P2528 style=TableText -->
有边界的比较判断或机制候选

<!-- source-paragraph:V82-P2529 style=TableText -->
L3

<!-- source-paragraph:V82-P2530 style=TableText -->
高责任强判断候选

<!-- source-paragraph:V82-P2531 style=TableText -->
高影响、公开、自动化、组织化、制度化或高权力密度

<!-- source-paragraph:V82-P2532 style=TableText -->
七闸与八件套通过后的强判断候选

<!-- source-paragraph:V82-P2533 style=BodyCJK -->
档位升高不是“更接近真理”，而是增加记录责任。证据覆盖下降、对象转换、反身性失控、申诉或反报复失效时必须降级。紧急也不能删除对象、保护或停止条件；等待代价高时，只能在相应授权外另提出最窄、可撤回、可监测的行动要求。

<!-- source-paragraph:V82-P2534 style=SecH2 -->
13.7　六项正式工具

<!-- source-paragraph:V82-P2535 style=TableHead -->
ID

<!-- source-paragraph:V82-P2536 style=TableHead -->
工具

<!-- source-paragraph:V82-P2537 style=TableHead -->
作用与边界

<!-- source-paragraph:V82-P2538 style=TableText -->
TOOL-EVIDENCE-LEDGER

<!-- source-paragraph:V82-P2539 style=TableText -->
来源—证据台账

<!-- source-paragraph:V82-P2540 style=TableText -->
分离来源、材料、观察、证据、反例、覆盖和不确定性；不证明命题

<!-- source-paragraph:V82-P2541 style=TableText -->
TOOL-OPEN-ASSERTION

<!-- source-paragraph:V82-P2542 style=TableText -->
开放断言记录

<!-- source-paragraph:V82-P2543 style=TableText -->
留下可质疑、可证伪、可撤回的临时判断靶点；不用作高责任处置

<!-- source-paragraph:V82-P2544 style=TableText -->
TOOL-CLAIM-VALIDATION

<!-- source-paragraph:V82-P2545 style=TableText -->
命题验证表

<!-- source-paragraph:V82-P2546 style=TableText -->
对命题类型、证据、反证、证伪条件、影响与上限逐项登记

<!-- source-paragraph:V82-P2547 style=TableText -->
TOOL-FORECAST-REGISTRY

<!-- source-paragraph:V82-P2548 style=TableText -->
前瞻登记

<!-- source-paragraph:V82-P2549 style=TableText -->
冻结预测、窗口、触发、早期信号、反向信号和修改目标

<!-- source-paragraph:V82-P2550 style=TableText -->
TOOL-STRESS-TEST

<!-- source-paragraph:V82-P2551 style=TableText -->
反例与尺度压力测试

<!-- source-paragraph:V82-P2552 style=TableText -->
用边界案例、对抗解释和尺度变化找失败位置并收缩范围

<!-- source-paragraph:V82-P2553 style=TableText -->
TOOL-AI-BOUNDARY

<!-- source-paragraph:V82-P2554 style=TableText -->
AI 输出边界

<!-- source-paragraph:V82-P2555 style=TableText -->
强制来源披露、缺失材料、人类责任人、不确定性、禁止用途和复核撤回

<!-- source-paragraph:V82-P2556 style=BodyCJK -->
证据台账不能把“有来源”写成“被支持”；开放断言不能代替命题验证；预测失败必须写回相关命题；内部压力测试只是一场风洞，不是外部经验支持。工具之间可以引用记录 ID，但不得互相循环自证。

<!-- source-paragraph:V82-P2557 style=SecH2 -->
13.8　AI 使用边界

<!-- source-paragraph:V82-P2558 style=BodyCJK -->
AI 可以整理材料、检查字段、比较版本、生成候选问题、列出替代解释和发现格式矛盾。AI 不得虚构来源、把训练记忆当作当前证据、替当事人表达同意、把沉默解释为同意、代替决策主体或授权机关、隐藏不确定性，也不得独立作出高风险现实决定。

<!-- source-paragraph:V82-P2559 style=BodyCJK -->
AI 输出必须说明：使用了哪些材料、缺什么、哪些内容是观察/推断/类比、谁承担最终判断责任、允许怎样使用、何时复核和撤回。涉及身份暴露、报复风险或正当不透明时，保护性省略必须与“没有证据”保持可区分。

<!-- source-paragraph:V82-P2560 style=SecH2 -->
13.9　运行记录与失败语义

<!-- source-paragraph:V82-P2561 style=BodyCJK -->
每次工具运行生成一个字段闭合的 flow_execution_record。它登记对象和尺度记录、L1-L3 档位、IT1-IT4 结果、IG1-IG7 结果、是否运行五闸十三步、是否触发 SJ1-SJ8、证据、替代解释、不确定性、输出类别、判断/行动上限、规范移交、申诉、回滚和状态。

<!-- source-paragraph:V82-P2562 style=BodyCJK -->
行动上限使用封闭输出上限格：description_only、diagnostic_only、requirements_only。每一档都固定可出现的输出类别，并且 can_authorize=false、can_execute=false；调用者不能在自由文本中自报“已经授权”，也不能自行扩展允许类别。action_requirements 只是对外部选择与授权程序提出所需条件，不是可执行命令。

<!-- source-paragraph:V82-P2563 style=BodyCJK -->
normative_handoff 中的选择记录、C12 闸与 J 授权只能写成规范缺失状态，或写成带 record_type、外部记录 ID、报告状态和独立 verification_ref 的外部核验引用。所有 record_id、verification_ref 和程序 ID 都必须是无首尾空白的外部引用；none、self、self:* 及其大小写或空白变体一律无效。selection:passed、C12:passed、J:authorized 之类字符串自报同样无效；工具只链接和核验外部记录，不在本记录中生成这些状态。

<!-- source-paragraph:V82-P2564 style=BodyCJK -->
结果状态要保持可区分：passed 表示该项记录门通过，failed 表示已运行但失败，not_run 表示因前闸或范围限制没有运行；unknown、not_applicable、not_observable 与 withheld_for_protection 仍是四种不同缺失状态。失败不能改写成不适用，保护性隐匿不能改写成不存在。

<!-- source-paragraph:V82-P2565 style=BodyCJK -->
运行记录的 authorization_effect 恒为 none。即使规范选择、C12、J 和 O 的外部引用均已存在，本记录也只是核对和移交它们，不自行铸造授权。所有已复核输出必须保留可达申诉与实际撤回/纠正路径；不能撤回的工具结论不得进入高影响难逆用途。

<!-- source-paragraph:V82-P2566 style=SecH2 -->
13.10　多圈层推演九闸

<!-- source-paragraph:V82-P2567 style=BodyCJK -->
七闸是解释与诊断的唯一主流程；当任务明确要求动态推演、条件前瞻或有限选择时，在其基础上展开九闸。九闸不得绕过七闸已经规定的对象、证据、受影响位置、权力、反身性、强判断程序和行动上限。

<!-- source-paragraph:V82-P2568 style=TableHead -->
闸

<!-- source-paragraph:V82-P2569 style=TableHead -->
核心检查

<!-- source-paragraph:V82-P2570 style=TableHead -->
失败输出

<!-- source-paragraph:V82-P2571 style=TableText -->
DF1 事实冻结

<!-- source-paragraph:V82-P2572 style=TableText -->
事件类型、来源、时间、证据截止和争议

<!-- source-paragraph:V82-P2573 style=TableText -->
事实问题清单

<!-- source-paragraph:V82-P2574 style=TableText -->
DF2 联合对象

<!-- source-paragraph:V82-P2575 style=TableText -->
行动者、圈层、关系、成员与 K

<!-- source-paragraph:V82-P2576 style=TableText -->
候选分组或单焦点退回

<!-- source-paragraph:V82-P2577 style=TableText -->
DF3 双通道与时钟

<!-- source-paragraph:V82-P2578 style=TableText -->
物质/体验—意义、五类时钟、未知

<!-- source-paragraph:V82-P2579 style=TableText -->
状态快照，不传播

<!-- source-paragraph:V82-P2580 style=TableText -->
DF4 机制传播

<!-- source-paragraph:V82-P2581 style=TableText -->
通道、阈值、时延、反馈和级联

<!-- source-paragraph:V82-P2582 style=TableText -->
候选机制与区分观察

<!-- source-paragraph:V82-P2583 style=TableText -->
DF5 路径分叉

<!-- source-paragraph:V82-P2584 style=TableText -->
条件、父子节点、早期与反向信号

<!-- source-paragraph:V82-P2585 style=TableText -->
并行路径，不强制排序

<!-- source-paragraph:V82-P2586 style=TableText -->
DF6 前瞻登记

<!-- source-paragraph:V82-P2587 style=TableText -->
目标、期限、简单基线、校准和回写

<!-- source-paragraph:V82-P2588 style=TableText -->
仅情景推演

<!-- source-paragraph:V82-P2589 style=TableText -->
DF7 规范选择

<!-- source-paragraph:V82-P2590 style=TableText -->
N、PF、受影响者、方案与不行动

<!-- source-paragraph:V82-P2591 style=TableText -->
需求清单，不推荐

<!-- source-paragraph:V82-P2592 style=TableText -->
DF8 授权与执行

<!-- source-paragraph:V82-P2593 style=TableText -->
J、O、责任、停止、回滚和补救

<!-- source-paragraph:V82-P2594 style=TableText -->
外部移交，不执行

<!-- source-paragraph:V82-P2595 style=TableText -->
DF9 结果回写

<!-- source-paragraph:V82-P2596 style=TableText -->
结果、基线比较、偏差、降级和退役

<!-- source-paragraph:V82-P2597 style=TableText -->
保留失败并开新版本

<!-- source-paragraph:V82-P2598 style=BodyCJK -->
工具在 DF2 可以提出圈层候选，在 DF5 可以提出变量候选，但任何候选都保持 candidate。DF6 未通过时，输出不能使用“将会”“预计命中”等前瞻语气；DF7 或 DF8 未通过时，输出不能给出可执行指令。DF9 不允许覆盖原运行。

<!-- source-paragraph:V82-P2599 style=SecH2 -->
13.11　AI 在动态运行中的边界

<!-- source-paragraph:V82-P2600 style=BodyCJK -->
AI 可以整理材料、发现字段缺口、生成竞争路径、检查合同一致性和计算已登记指标。AI 不能验证现实事件、诊断人格、替当事人披露信息、决定圈层边界、把模拟当事实、选择价值前提或签发授权。对 AI 自动提出的变量，系统必须记录来源为模型候选、最小检验和禁止用途；没有外部证据前不得升级。

## Canonical Records

<!-- canonical-records:start -->
```json
{
  "paragraphs": [
    {
      "anchor": "V82-P2349",
      "ordinal": 2349,
      "style": "PartTitle",
      "text": "第十三部分　接口与工具"
    },
    {
      "anchor": "V82-P2350",
      "ordinal": 2350,
      "style": "BodyCJK",
      "text": "本部分把此前十二部分定义的对象、命题、尺度、机制、行动者、多圈层联合状态和动态推演要求转换为可观察、可质疑、可复核、可撤回的有限判断。它不新增世界事实，也不把表格完整度当作事实成立。进入工具流前，必须已有 D0 候选对象记录和九轴尺度记录；对象、边界、尺度、时间窗、同一性判据或用途改变时，已有判断不得平移沿用。"
    },
    {
      "anchor": "V82-P2351",
      "ordinal": 2351,
      "style": "BodyCJK",
      "text": "工具流程采用两级结构：七闸是唯一主流程，五闸十三步是诊断展开层。七闸回答判断能否进入下一层；五闸十三步在复杂案例中展开需要提交的材料，但不另行出具与七闸竞争的“通过”结论，也不产生第二套流程状态。"
    },
    {
      "anchor": "V82-P2352",
      "ordinal": 2352,
      "style": "BodyCJK",
      "text": "最重要的边界是：工具层不产生授权。流程、证据、强判断八件套全部完成，也只产生描述、候选机制、比较判断、强判断候选或行动要求。现实行动仍须另经结构化选择记录、C12 十组件桥、同一条有效 J 原子授权以及 O1-O4；工具输出不能替代其中任何一项。"
    },
    {
      "anchor": "V82-P2353",
      "ordinal": 2353,
      "style": "SecH2",
      "text": "13.1　四次转换"
    },
    {
      "anchor": "V82-P2354",
      "ordinal": 2354,
      "style": "BodyCJK",
      "text": "四次转换不是把理论词换成现实标签，而是逐次增加记录责任。任一步失败，输出停在该步之前，不能靠后一步的格式完整补救。"
    },
    {
      "anchor": "V82-P2355",
      "ordinal": 2355,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2356",
      "ordinal": 2356,
      "style": "TableHead",
      "text": "转换"
    },
    {
      "anchor": "V82-P2357",
      "ordinal": 2357,
      "style": "TableHead",
      "text": "必须得到什么"
    },
    {
      "anchor": "V82-P2358",
      "ordinal": 2358,
      "style": "TableHead",
      "text": "失败时停在哪里"
    },
    {
      "anchor": "V82-P2359",
      "ordinal": 2359,
      "style": "TableText",
      "text": "IT1"
    },
    {
      "anchor": "V82-P2360",
      "ordinal": 2360,
      "style": "TableText",
      "text": "结构变量到可观察信号"
    },
    {
      "anchor": "V82-P2361",
      "ordinal": 2361,
      "style": "TableText",
      "text": "对象、尺度、观察位置、时间窗、测量协议和缺失状态明确的信号记录"
    },
    {
      "anchor": "V82-P2362",
      "ordinal": 2362,
      "style": "TableText",
      "text": "概念映射或材料缺口"
    },
    {
      "anchor": "V82-P2363",
      "ordinal": 2363,
      "style": "TableText",
      "text": "IT2"
    },
    {
      "anchor": "V82-P2364",
      "ordinal": 2364,
      "style": "TableText",
      "text": "可观察信号到证据强度"
    },
    {
      "anchor": "V82-P2365",
      "ordinal": 2365,
      "style": "TableText",
      "text": "来源、观察、比较条件、覆盖、反例、替代解释和不确定性分开的证据记录"
    },
    {
      "anchor": "V82-P2366",
      "ordinal": 2366,
      "style": "TableText",
      "text": "未分级材料或待检验假设"
    },
    {
      "anchor": "V82-P2367",
      "ordinal": 2367,
      "style": "TableText",
      "text": "IT3"
    },
    {
      "anchor": "V82-P2368",
      "ordinal": 2368,
      "style": "TableText",
      "text": "证据强度到判断等级"
    },
    {
      "anchor": "V82-P2369",
      "ordinal": 2369,
      "style": "TableText",
      "text": "有命题合同、适用边界、反向条件、证伪条件和撤回条件的判断"
    },
    {
      "anchor": "V82-P2370",
      "ordinal": 2370,
      "style": "TableText",
      "text": "候选解释或观察意见"
    },
    {
      "anchor": "V82-P2371",
      "ordinal": 2371,
      "style": "TableText",
      "text": "IT4"
    },
    {
      "anchor": "V82-P2372",
      "ordinal": 2372,
      "style": "TableText",
      "text": "判断等级到行动要求与上限"
    },
    {
      "anchor": "V82-P2373",
      "ordinal": 2373,
      "style": "TableText",
      "text": "受影响位置、保护底板、禁止动作、停止、申诉、回滚及尚缺 N/J/O/C12 的清单"
    },
    {
      "anchor": "V82-P2374",
      "ordinal": 2374,
      "style": "TableText",
      "text": "描述、补证或不行动要求"
    },
    {
      "anchor": "V82-P2375",
      "ordinal": 2375,
      "style": "BodyCJK",
      "text": "IT1 防止把结构叙事当成观察事实；IT2 防止把出处、材料或表态直接当成证据；IT3 防止把相关、类比或单一机制故事升级为结论；IT4 防止从事实判断直接跳到处置。四次转换全部通过也不改变授权状态。"
    },
    {
      "anchor": "V82-P2376",
      "ordinal": 2376,
      "style": "BodyCJK",
      "text": "任何 IT 转换失败，后续转换只能记 not_run，本次运行的输出上限立即降到描述或候选机制，不得输出 comparative_judgment、strong_judgment 或 action_requirements。后续 not_run 只是保留失败链，不能重新抬高输出上限；八件套齐全也不能补回转换链上的断口。"
    },
    {
      "anchor": "V82-P2377",
      "ordinal": 2377,
      "style": "SecH2",
      "text": "13.2　通用原语与人类变量接口(11+11)的调用方式"
    },
    {
      "anchor": "V82-P2378",
      "ordinal": 2378,
      "style": "BodyCJK",
      "text": "第七部分的 HV01-HV11 是人类结构化世界的十一项接口；第三部分的 U01-U11 是通用结构原语。工具层可以在同一案例中并列调用二者，但不把编号相同、数量相同或问题相似解释为一一等价。"
    },
    {
      "anchor": "V82-P2379",
      "ordinal": 2379,
      "style": "BodyCJK",
      "text": "调用时至少登记：通用或人类接口 ID、有效对象、九轴尺度、所选支持路由、实例证据、替代解释、缺失状态、判断上限与行动上限。H1/H4/H5 只能经各自 H-instance 进入指定路由；G1-G4 只能经结果前冻结的 G-instance 支持经验主张。接口卡能提出问题，却不能因字段填满而证明对象事实。"
    },
    {
      "anchor": "V82-P2380",
      "ordinal": 2380,
      "style": "SecH2",
      "text": "13.3　七闸：唯一主流程"
    },
    {
      "anchor": "V82-P2381",
      "ordinal": 2381,
      "style": "BodyCJK",
      "text": "七闸依次运行。某一闸失败后，后续闸只能记 not_run，本次运行的输出上限同时降到描述或候选机制，不得输出比较判断、强判断或行动要求。后续 not_run 不能抬高失败闸已经压低的上限，也不能一边承认对象或证据未过闸，一边让后续程序自报通过。对象、证据版本、受影响位置或用途发生实质变化时，从最早受影响的闸重新运行。"
    },
    {
      "anchor": "V82-P2382",
      "ordinal": 2382,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2383",
      "ordinal": 2383,
      "style": "TableHead",
      "text": "闸门"
    },
    {
      "anchor": "V82-P2384",
      "ordinal": 2384,
      "style": "TableHead",
      "text": "核心问题"
    },
    {
      "anchor": "V82-P2385",
      "ordinal": 2385,
      "style": "TableHead",
      "text": "未通过时的输出上限"
    },
    {
      "anchor": "V82-P2386",
      "ordinal": 2386,
      "style": "TableText",
      "text": "IG1"
    },
    {
      "anchor": "V82-P2387",
      "ordinal": 2387,
      "style": "TableText",
      "text": "有效对象闸"
    },
    {
      "anchor": "V82-P2388",
      "ordinal": 2388,
      "style": "TableText",
      "text": "对象、边界、九轴尺度、时间窗与 K 是否支持本次判断？"
    },
    {
      "anchor": "V82-P2389",
      "ordinal": 2389,
      "style": "TableText",
      "text": "重新界定对象、尺度未知或对象转换复核"
    },
    {
      "anchor": "V82-P2390",
      "ordinal": 2390,
      "style": "TableText",
      "text": "IG2"
    },
    {
      "anchor": "V82-P2391",
      "ordinal": 2391,
      "style": "TableText",
      "text": "证据追踪闸"
    },
    {
      "anchor": "V82-P2392",
      "ordinal": 2392,
      "style": "TableText",
      "text": "来源、材料、观察、证据、反例、案例与判断是否分开可回溯？"
    },
    {
      "anchor": "V82-P2393",
      "ordinal": 2393,
      "style": "TableText",
      "text": "材料整理、候选问题或待检验假设"
    },
    {
      "anchor": "V82-P2394",
      "ordinal": 2394,
      "style": "TableText",
      "text": "IG3"
    },
    {
      "anchor": "V82-P2395",
      "ordinal": 2395,
      "style": "TableText",
      "text": "受影响位置闸"
    },
    {
      "anchor": "V82-P2396",
      "ordinal": 2396,
      "style": "TableText",
      "text": "哪些直接、间接、二阶、跨域与跨期位置会改变处境？"
    },
    {
      "anchor": "V82-P2397",
      "ordinal": 2397,
      "style": "TableText",
      "text": "补充影响核算；暂停强判断和高影响用途"
    },
    {
      "anchor": "V82-P2398",
      "ordinal": 2398,
      "style": "TableText",
      "text": "IG4"
    },
    {
      "anchor": "V82-P2399",
      "ordinal": 2399,
      "style": "TableText",
      "text": "权力与反报复闸"
    },
    {
      "anchor": "V82-P2400",
      "ordinal": 2400,
      "style": "TableText",
      "text": "低权力位置能否安全补证、反驳、拒绝、停止和申诉？"
    },
    {
      "anchor": "V82-P2401",
      "ordinal": 2401,
      "style": "TableText",
      "text": "不得因沉默作不利推断；降低发布与判断档位"
    },
    {
      "anchor": "V82-P2402",
      "ordinal": 2402,
      "style": "TableText",
      "text": "IG5"
    },
    {
      "anchor": "V82-P2403",
      "ordinal": 2403,
      "style": "TableText",
      "text": "中介与反身性闸"
    },
    {
      "anchor": "V82-P2404",
      "ordinal": 2404,
      "style": "TableText",
      "text": "指标、平台、AI、公开评价或诊断行为是否改变证据和对象？"
    },
    {
      "anchor": "V82-P2405",
      "ordinal": 2405,
      "style": "TableText",
      "text": "高反身性未收束；改写为条件状态转移"
    },
    {
      "anchor": "V82-P2406",
      "ordinal": 2406,
      "style": "TableText",
      "text": "IG6"
    },
    {
      "anchor": "V82-P2407",
      "ordinal": 2407,
      "style": "TableText",
      "text": "强判断程序闸"
    },
    {
      "anchor": "V82-P2408",
      "ordinal": 2408,
      "style": "TableText",
      "text": "高影响、公开或组织化判断是否完整提交 SJ1-SJ8？"
    },
    {
      "anchor": "V82-P2409",
      "ordinal": 2409,
      "style": "TableText",
      "text": "内部假设、开放断言或候选机制；不得形成比较判断"
    },
    {
      "anchor": "V82-P2410",
      "ordinal": 2410,
      "style": "TableText",
      "text": "IG7"
    },
    {
      "anchor": "V82-P2411",
      "ordinal": 2411,
      "style": "TableText",
      "text": "行动上限闸"
    },
    {
      "anchor": "V82-P2412",
      "ordinal": 2412,
      "style": "TableText",
      "text": "最多只能提出什么要求，哪些动作禁止，何时停止、申诉和回滚？"
    },
    {
      "anchor": "V82-P2413",
      "ordinal": 2413,
      "style": "TableText",
      "text": "描述、证据缺口、不行动或继续审议"
    },
    {
      "anchor": "V82-P2414",
      "ordinal": 2414,
      "style": "BodyCJK",
      "text": "七闸全过不表示结论为真，只表示相应记录门没有缺口。经验命题仍由其命题合同和实例证据判定；规范目标仍需明示 N 前提；现实行动仍需选择、C12、J 与 O 程序。特别是 IG7 只能记录外部规范层与授权层是否具备，不能由工具流自己写成“已授权”。"
    },
    {
      "anchor": "V82-P2415",
      "ordinal": 2415,
      "style": "BodyCJK",
      "text": "IG6 有一条专门适用性规则：普通 L1/L2 输出可以把它记为 not_applicable，但必须写明为什么本次不触发强判断程序，且这不会阻断 IG7；一旦 IG6 记为 passed，同一运行记录必须绑定完整、逐项 passed 的 SJ1—SJ8。用“已检查”字符串或空理由不能代替八项结果。"
    },
    {
      "anchor": "V82-P2416",
      "ordinal": 2416,
      "style": "SecH2",
      "text": "13.4　五闸十三步：诊断展开层"
    },
    {
      "anchor": "V82-P2417",
      "ordinal": 2417,
      "style": "BodyCJK",
      "text": "当对象复杂、高责任、高反身性，或七闸需要展开取证时，运行五闸十三步。五闸是展开过程的局部检查，不生成第二套主流程状态。"
    },
    {
      "anchor": "V82-P2418",
      "ordinal": 2418,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2419",
      "ordinal": 2419,
      "style": "TableHead",
      "text": "展开闸"
    },
    {
      "anchor": "V82-P2420",
      "ordinal": 2420,
      "style": "TableHead",
      "text": "必须展开的材料"
    },
    {
      "anchor": "V82-P2421",
      "ordinal": 2421,
      "style": "TableHead",
      "text": "对应主闸"
    },
    {
      "anchor": "V82-P2422",
      "ordinal": 2422,
      "style": "TableText",
      "text": "FG1"
    },
    {
      "anchor": "V82-P2423",
      "ordinal": 2423,
      "style": "TableText",
      "text": "对象闸"
    },
    {
      "anchor": "V82-P2424",
      "ordinal": 2424,
      "style": "TableText",
      "text": "对象、边界、尺度、时间窗"
    },
    {
      "anchor": "V82-P2425",
      "ordinal": 2425,
      "style": "TableText",
      "text": "IG1"
    },
    {
      "anchor": "V82-P2426",
      "ordinal": 2426,
      "style": "TableText",
      "text": "FG2"
    },
    {
      "anchor": "V82-P2427",
      "ordinal": 2427,
      "style": "TableText",
      "text": "证据闸"
    },
    {
      "anchor": "V82-P2428",
      "ordinal": 2428,
      "style": "TableText",
      "text": "信号成本、来源、权重、复核"
    },
    {
      "anchor": "V82-P2429",
      "ordinal": 2429,
      "style": "TableText",
      "text": "IG2"
    },
    {
      "anchor": "V82-P2430",
      "ordinal": 2430,
      "style": "TableText",
      "text": "FG3"
    },
    {
      "anchor": "V82-P2431",
      "ordinal": 2431,
      "style": "TableText",
      "text": "尺度闸"
    },
    {
      "anchor": "V82-P2432",
      "ordinal": 2432,
      "style": "TableText",
      "text": "九轴尺度、尺度内对象与证据、尺度变化"
    },
    {
      "anchor": "V82-P2433",
      "ordinal": 2433,
      "style": "TableText",
      "text": "IG1、IG2"
    },
    {
      "anchor": "V82-P2434",
      "ordinal": 2434,
      "style": "TableText",
      "text": "FG4"
    },
    {
      "anchor": "V82-P2435",
      "ordinal": 2435,
      "style": "TableText",
      "text": "责任闸"
    },
    {
      "anchor": "V82-P2436",
      "ordinal": 2436,
      "style": "TableText",
      "text": "权利/资源影响、反向条件、修复窗口、申诉复核"
    },
    {
      "anchor": "V82-P2437",
      "ordinal": 2437,
      "style": "TableText",
      "text": "IG3、IG4、IG6"
    },
    {
      "anchor": "V82-P2438",
      "ordinal": 2438,
      "style": "TableText",
      "text": "FG5"
    },
    {
      "anchor": "V82-P2439",
      "ordinal": 2439,
      "style": "TableText",
      "text": "观测闸"
    },
    {
      "anchor": "V82-P2440",
      "ordinal": 2440,
      "style": "TableText",
      "text": "观察前基线、观察中反应、发布后反应、递归封顶"
    },
    {
      "anchor": "V82-P2441",
      "ordinal": 2441,
      "style": "TableText",
      "text": "IG5"
    },
    {
      "anchor": "V82-P2442",
      "ordinal": 2442,
      "style": "BodyCJK",
      "text": "十三步按现实问题到写回的顺序形成一条可审计工作链："
    },
    {
      "anchor": "V82-P2443",
      "ordinal": 2443,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2444",
      "ordinal": 2444,
      "style": "TableHead",
      "text": "步骤"
    },
    {
      "anchor": "V82-P2445",
      "ordinal": 2445,
      "style": "TableHead",
      "text": "最小产物"
    },
    {
      "anchor": "V82-P2446",
      "ordinal": 2446,
      "style": "TableText",
      "text": "DS01"
    },
    {
      "anchor": "V82-P2447",
      "ordinal": 2447,
      "style": "TableText",
      "text": "问题入口"
    },
    {
      "anchor": "V82-P2448",
      "ordinal": 2448,
      "style": "TableText",
      "text": "不使用框架术语的现实问题、请求者和用途"
    },
    {
      "anchor": "V82-P2449",
      "ordinal": 2449,
      "style": "TableText",
      "text": "DS02"
    },
    {
      "anchor": "V82-P2450",
      "ordinal": 2450,
      "style": "TableText",
      "text": "对象与边界"
    },
    {
      "anchor": "V82-P2451",
      "ordinal": 2451,
      "style": "TableText",
      "text": "有效对象、子系统、上级环境和外部通道"
    },
    {
      "anchor": "V82-P2452",
      "ordinal": 2452,
      "style": "TableText",
      "text": "DS03"
    },
    {
      "anchor": "V82-P2453",
      "ordinal": 2453,
      "style": "TableText",
      "text": "信号分层"
    },
    {
      "anchor": "V82-P2454",
      "ordinal": 2454,
      "style": "TableText",
      "text": "事实、行为、资源、反馈、叙事、感受、推测和噪声分栏"
    },
    {
      "anchor": "V82-P2455",
      "ordinal": 2455,
      "style": "TableText",
      "text": "DS04"
    },
    {
      "anchor": "V82-P2456",
      "ordinal": 2456,
      "style": "TableText",
      "text": "观测参与登记"
    },
    {
      "anchor": "V82-P2457",
      "ordinal": 2457,
      "style": "TableText",
      "text": "被观察知情、观察者权力、发布影响和候选反应"
    },
    {
      "anchor": "V82-P2458",
      "ordinal": 2458,
      "style": "TableText",
      "text": "DS05"
    },
    {
      "anchor": "V82-P2459",
      "ordinal": 2459,
      "style": "TableText",
      "text": "主导约束"
    },
    {
      "anchor": "V82-P2460",
      "ordinal": 2460,
      "style": "TableText",
      "text": "候选约束、所选约束、选择证据和竞争约束"
    },
    {
      "anchor": "V82-P2461",
      "ordinal": 2461,
      "style": "TableText",
      "text": "DS06"
    },
    {
      "anchor": "V82-P2462",
      "ordinal": 2462,
      "style": "TableText",
      "text": "状态与窗口"
    },
    {
      "anchor": "V82-P2463",
      "ordinal": 2463,
      "style": "TableText",
      "text": "S0-S6 原型引用、状态内位置、并行子系统和反向条件"
    },
    {
      "anchor": "V82-P2464",
      "ordinal": 2464,
      "style": "TableText",
      "text": "DS07"
    },
    {
      "anchor": "V82-P2465",
      "ordinal": 2465,
      "style": "TableText",
      "text": "核心结构扫描"
    },
    {
      "anchor": "V82-P2466",
      "ordinal": 2466,
      "style": "TableText",
      "text": "锚点、承接层、传导链、边界和反馈写回"
    },
    {
      "anchor": "V82-P2467",
      "ordinal": 2467,
      "style": "TableText",
      "text": "DS08"
    },
    {
      "anchor": "V82-P2468",
      "ordinal": 2468,
      "style": "TableText",
      "text": "关键保护变量"
    },
    {
      "anchor": "V82-P2469",
      "ordinal": 2469,
      "style": "TableText",
      "text": "受保护变量、受损路径、资源、冗余和修复/回流路径"
    },
    {
      "anchor": "V82-P2470",
      "ordinal": 2470,
      "style": "TableText",
      "text": "DS09"
    },
    {
      "anchor": "V82-P2471",
      "ordinal": 2471,
      "style": "TableText",
      "text": "承接与偿付"
    },
    {
      "anchor": "V82-P2472",
      "ordinal": 2472,
      "style": "TableText",
      "text": "成本承担者、回流获得者、停止权、长期透支与损害转移"
    },
    {
      "anchor": "V82-P2473",
      "ordinal": 2473,
      "style": "TableText",
      "text": "DS10"
    },
    {
      "anchor": "V82-P2474",
      "ordinal": 2474,
      "style": "TableText",
      "text": "隐患与边界类型"
    },
    {
      "anchor": "V82-P2475",
      "ordinal": 2475,
      "style": "TableText",
      "text": "维护债、快慢错配、指标替代、摘要失真和对象转换候选"
    },
    {
      "anchor": "V82-P2476",
      "ordinal": 2476,
      "style": "TableText",
      "text": "DS11"
    },
    {
      "anchor": "V82-P2477",
      "ordinal": 2477,
      "style": "TableText",
      "text": "机制候选"
    },
    {
      "anchor": "V82-P2478",
      "ordinal": 2478,
      "style": "TableText",
      "text": "至少两个竞争机制、各自所需证据、削弱证据和淘汰规则"
    },
    {
      "anchor": "V82-P2479",
      "ordinal": 2479,
      "style": "TableText",
      "text": "DS12"
    },
    {
      "anchor": "V82-P2480",
      "ordinal": 2480,
      "style": "TableText",
      "text": "分支预判"
    },
    {
      "anchor": "V82-P2481",
      "ordinal": 2481,
      "style": "TableText",
      "text": "触发、早期信号、反向条件、修复窗口和最低行动要求"
    },
    {
      "anchor": "V82-P2482",
      "ordinal": 2482,
      "style": "TableText",
      "text": "DS13"
    },
    {
      "anchor": "V82-P2483",
      "ordinal": 2483,
      "style": "TableText",
      "text": "输出与写回"
    },
    {
      "anchor": "V82-P2484",
      "ordinal": 2484,
      "style": "TableText",
      "text": "现实语言输出、修改触发器、记录范围、复核、撤回和回滚"
    },
    {
      "anchor": "V82-P2485",
      "ordinal": 2485,
      "style": "BodyCJK",
      "text": "DS06 只能引用人类状态原型，不能把 S0-S6 写成成熟度或命运。DS08 发现重要保护变量，只能生成保护需求；DS09 发现承接或透支，不能生成牺牲义务或完整责任；DS11 的机制候选不得跨过因果合同；DS12 的分支不是确定未来；DS13 没有复核和撤回时，不得把判断写入组织记录、资格、分配或公共记忆。"
    },
    {
      "anchor": "V82-P2486",
      "ordinal": 2486,
      "style": "SecH2",
      "text": "13.5　强判断八件套"
    },
    {
      "anchor": "V82-P2487",
      "ordinal": 2487,
      "style": "BodyCJK",
      "text": "强判断是可能影响处置、资格、声誉、资源、权利、公共记忆，或将被公开、自动化、组织化、制度化使用的判断。只有 L3 且七闸全过、下列八项逐项通过时，才可登记“强判断候选”；它仍不是现实行动授权。"
    },
    {
      "anchor": "V82-P2488",
      "ordinal": 2488,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2489",
      "ordinal": 2489,
      "style": "TableHead",
      "text": "组件"
    },
    {
      "anchor": "V82-P2490",
      "ordinal": 2490,
      "style": "TableHead",
      "text": "必须回答什么"
    },
    {
      "anchor": "V82-P2491",
      "ordinal": 2491,
      "style": "TableText",
      "text": "SJ1"
    },
    {
      "anchor": "V82-P2492",
      "ordinal": 2492,
      "style": "TableText",
      "text": "反向条件"
    },
    {
      "anchor": "V82-P2493",
      "ordinal": 2493,
      "style": "TableText",
      "text": "出现什么情况会削弱、反转或撤回判断？"
    },
    {
      "anchor": "V82-P2494",
      "ordinal": 2494,
      "style": "TableText",
      "text": "SJ2"
    },
    {
      "anchor": "V82-P2495",
      "ordinal": 2495,
      "style": "TableText",
      "text": "修复窗口"
    },
    {
      "anchor": "V82-P2496",
      "ordinal": 2496,
      "style": "TableText",
      "text": "窗口何在、根据何在、何时失效？"
    },
    {
      "anchor": "V82-P2497",
      "ordinal": 2497,
      "style": "TableText",
      "text": "SJ3"
    },
    {
      "anchor": "V82-P2498",
      "ordinal": 2498,
      "style": "TableText",
      "text": "证据要求"
    },
    {
      "anchor": "V82-P2499",
      "ordinal": 2499,
      "style": "TableText",
      "text": "支持、缺失和反向证据分别是什么？"
    },
    {
      "anchor": "V82-P2500",
      "ordinal": 2500,
      "style": "TableText",
      "text": "SJ4"
    },
    {
      "anchor": "V82-P2501",
      "ordinal": 2501,
      "style": "TableText",
      "text": "申诉入口"
    },
    {
      "anchor": "V82-P2502",
      "ordinal": 2502,
      "style": "TableText",
      "text": "谁可进入、谁负责、时限多长、能否改变结果？"
    },
    {
      "anchor": "V82-P2503",
      "ordinal": 2503,
      "style": "TableText",
      "text": "SJ5"
    },
    {
      "anchor": "V82-P2504",
      "ordinal": 2504,
      "style": "TableText",
      "text": "反报复保护"
    },
    {
      "anchor": "V82-P2505",
      "ordinal": 2505,
      "style": "TableText",
      "text": "哪些行为受保护、如何监测、如何独立报告和补救？"
    },
    {
      "anchor": "V82-P2506",
      "ordinal": 2506,
      "style": "TableText",
      "text": "SJ6"
    },
    {
      "anchor": "V82-P2507",
      "ordinal": 2507,
      "style": "TableText",
      "text": "证据补充权"
    },
    {
      "anchor": "V82-P2508",
      "ordinal": 2508,
      "style": "TableText",
      "text": "如何补证、纠正版本并同步下游？"
    },
    {
      "anchor": "V82-P2509",
      "ordinal": 2509,
      "style": "TableText",
      "text": "SJ7"
    },
    {
      "anchor": "V82-P2510",
      "ordinal": 2510,
      "style": "TableText",
      "text": "外部复核触发"
    },
    {
      "anchor": "V82-P2511",
      "ordinal": 2511,
      "style": "TableText",
      "text": "何时触发、谁独立复核、能否访问材料和停止结果？"
    },
    {
      "anchor": "V82-P2512",
      "ordinal": 2512,
      "style": "TableText",
      "text": "SJ8"
    },
    {
      "anchor": "V82-P2513",
      "ordinal": 2513,
      "style": "TableText",
      "text": "回滚与写回"
    },
    {
      "anchor": "V82-P2514",
      "ordinal": 2514,
      "style": "TableText",
      "text": "回到哪个状态、谁修复、哪个版本权威、如何同步？"
    },
    {
      "anchor": "V82-P2515",
      "ordinal": 2515,
      "style": "BodyCJK",
      "text": "任何一项缺失，IG6 失败，输出降为内部假设、开放断言或候选机制，不得保留 L2 比较判断。申诉入口若不能改变记录或行动，不算有效申诉；外部名义不等于独立；声明、道歉或新版本发布不等于实际回滚和修复。"
    },
    {
      "anchor": "V82-P2516",
      "ordinal": 2516,
      "style": "SecH2",
      "text": "13.6　诊断档位"
    },
    {
      "anchor": "V82-P2517",
      "ordinal": 2517,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2518",
      "ordinal": 2518,
      "style": "TableHead",
      "text": "档位"
    },
    {
      "anchor": "V82-P2519",
      "ordinal": 2519,
      "style": "TableHead",
      "text": "适用"
    },
    {
      "anchor": "V82-P2520",
      "ordinal": 2520,
      "style": "TableHead",
      "text": "输出上限"
    },
    {
      "anchor": "V82-P2521",
      "ordinal": 2521,
      "style": "TableText",
      "text": "L1"
    },
    {
      "anchor": "V82-P2522",
      "ordinal": 2522,
      "style": "TableText",
      "text": "轻量描述与试探问题"
    },
    {
      "anchor": "V82-P2523",
      "ordinal": 2523,
      "style": "TableText",
      "text": "低复杂、低影响、可逆且信息有限"
    },
    {
      "anchor": "V82-P2524",
      "ordinal": 2524,
      "style": "TableText",
      "text": "描述、问题和下一观察"
    },
    {
      "anchor": "V82-P2525",
      "ordinal": 2525,
      "style": "TableText",
      "text": "L2"
    },
    {
      "anchor": "V82-P2526",
      "ordinal": 2526,
      "style": "TableText",
      "text": "标准可复核判断"
    },
    {
      "anchor": "V82-P2527",
      "ordinal": 2527,
      "style": "TableText",
      "text": "需要结构比较但不进入高责任处置"
    },
    {
      "anchor": "V82-P2528",
      "ordinal": 2528,
      "style": "TableText",
      "text": "有边界的比较判断或机制候选"
    },
    {
      "anchor": "V82-P2529",
      "ordinal": 2529,
      "style": "TableText",
      "text": "L3"
    },
    {
      "anchor": "V82-P2530",
      "ordinal": 2530,
      "style": "TableText",
      "text": "高责任强判断候选"
    },
    {
      "anchor": "V82-P2531",
      "ordinal": 2531,
      "style": "TableText",
      "text": "高影响、公开、自动化、组织化、制度化或高权力密度"
    },
    {
      "anchor": "V82-P2532",
      "ordinal": 2532,
      "style": "TableText",
      "text": "七闸与八件套通过后的强判断候选"
    },
    {
      "anchor": "V82-P2533",
      "ordinal": 2533,
      "style": "BodyCJK",
      "text": "档位升高不是“更接近真理”，而是增加记录责任。证据覆盖下降、对象转换、反身性失控、申诉或反报复失效时必须降级。紧急也不能删除对象、保护或停止条件；等待代价高时，只能在相应授权外另提出最窄、可撤回、可监测的行动要求。"
    },
    {
      "anchor": "V82-P2534",
      "ordinal": 2534,
      "style": "SecH2",
      "text": "13.7　六项正式工具"
    },
    {
      "anchor": "V82-P2535",
      "ordinal": 2535,
      "style": "TableHead",
      "text": "ID"
    },
    {
      "anchor": "V82-P2536",
      "ordinal": 2536,
      "style": "TableHead",
      "text": "工具"
    },
    {
      "anchor": "V82-P2537",
      "ordinal": 2537,
      "style": "TableHead",
      "text": "作用与边界"
    },
    {
      "anchor": "V82-P2538",
      "ordinal": 2538,
      "style": "TableText",
      "text": "TOOL-EVIDENCE-LEDGER"
    },
    {
      "anchor": "V82-P2539",
      "ordinal": 2539,
      "style": "TableText",
      "text": "来源—证据台账"
    },
    {
      "anchor": "V82-P2540",
      "ordinal": 2540,
      "style": "TableText",
      "text": "分离来源、材料、观察、证据、反例、覆盖和不确定性；不证明命题"
    },
    {
      "anchor": "V82-P2541",
      "ordinal": 2541,
      "style": "TableText",
      "text": "TOOL-OPEN-ASSERTION"
    },
    {
      "anchor": "V82-P2542",
      "ordinal": 2542,
      "style": "TableText",
      "text": "开放断言记录"
    },
    {
      "anchor": "V82-P2543",
      "ordinal": 2543,
      "style": "TableText",
      "text": "留下可质疑、可证伪、可撤回的临时判断靶点；不用作高责任处置"
    },
    {
      "anchor": "V82-P2544",
      "ordinal": 2544,
      "style": "TableText",
      "text": "TOOL-CLAIM-VALIDATION"
    },
    {
      "anchor": "V82-P2545",
      "ordinal": 2545,
      "style": "TableText",
      "text": "命题验证表"
    },
    {
      "anchor": "V82-P2546",
      "ordinal": 2546,
      "style": "TableText",
      "text": "对命题类型、证据、反证、证伪条件、影响与上限逐项登记"
    },
    {
      "anchor": "V82-P2547",
      "ordinal": 2547,
      "style": "TableText",
      "text": "TOOL-FORECAST-REGISTRY"
    },
    {
      "anchor": "V82-P2548",
      "ordinal": 2548,
      "style": "TableText",
      "text": "前瞻登记"
    },
    {
      "anchor": "V82-P2549",
      "ordinal": 2549,
      "style": "TableText",
      "text": "冻结预测、窗口、触发、早期信号、反向信号和修改目标"
    },
    {
      "anchor": "V82-P2550",
      "ordinal": 2550,
      "style": "TableText",
      "text": "TOOL-STRESS-TEST"
    },
    {
      "anchor": "V82-P2551",
      "ordinal": 2551,
      "style": "TableText",
      "text": "反例与尺度压力测试"
    },
    {
      "anchor": "V82-P2552",
      "ordinal": 2552,
      "style": "TableText",
      "text": "用边界案例、对抗解释和尺度变化找失败位置并收缩范围"
    },
    {
      "anchor": "V82-P2553",
      "ordinal": 2553,
      "style": "TableText",
      "text": "TOOL-AI-BOUNDARY"
    },
    {
      "anchor": "V82-P2554",
      "ordinal": 2554,
      "style": "TableText",
      "text": "AI 输出边界"
    },
    {
      "anchor": "V82-P2555",
      "ordinal": 2555,
      "style": "TableText",
      "text": "强制来源披露、缺失材料、人类责任人、不确定性、禁止用途和复核撤回"
    },
    {
      "anchor": "V82-P2556",
      "ordinal": 2556,
      "style": "BodyCJK",
      "text": "证据台账不能把“有来源”写成“被支持”；开放断言不能代替命题验证；预测失败必须写回相关命题；内部压力测试只是一场风洞，不是外部经验支持。工具之间可以引用记录 ID，但不得互相循环自证。"
    },
    {
      "anchor": "V82-P2557",
      "ordinal": 2557,
      "style": "SecH2",
      "text": "13.8　AI 使用边界"
    },
    {
      "anchor": "V82-P2558",
      "ordinal": 2558,
      "style": "BodyCJK",
      "text": "AI 可以整理材料、检查字段、比较版本、生成候选问题、列出替代解释和发现格式矛盾。AI 不得虚构来源、把训练记忆当作当前证据、替当事人表达同意、把沉默解释为同意、代替决策主体或授权机关、隐藏不确定性，也不得独立作出高风险现实决定。"
    },
    {
      "anchor": "V82-P2559",
      "ordinal": 2559,
      "style": "BodyCJK",
      "text": "AI 输出必须说明：使用了哪些材料、缺什么、哪些内容是观察/推断/类比、谁承担最终判断责任、允许怎样使用、何时复核和撤回。涉及身份暴露、报复风险或正当不透明时，保护性省略必须与“没有证据”保持可区分。"
    },
    {
      "anchor": "V82-P2560",
      "ordinal": 2560,
      "style": "SecH2",
      "text": "13.9　运行记录与失败语义"
    },
    {
      "anchor": "V82-P2561",
      "ordinal": 2561,
      "style": "BodyCJK",
      "text": "每次工具运行生成一个字段闭合的 flow_execution_record。它登记对象和尺度记录、L1-L3 档位、IT1-IT4 结果、IG1-IG7 结果、是否运行五闸十三步、是否触发 SJ1-SJ8、证据、替代解释、不确定性、输出类别、判断/行动上限、规范移交、申诉、回滚和状态。"
    },
    {
      "anchor": "V82-P2562",
      "ordinal": 2562,
      "style": "BodyCJK",
      "text": "行动上限使用封闭输出上限格：description_only、diagnostic_only、requirements_only。每一档都固定可出现的输出类别，并且 can_authorize=false、can_execute=false；调用者不能在自由文本中自报“已经授权”，也不能自行扩展允许类别。action_requirements 只是对外部选择与授权程序提出所需条件，不是可执行命令。"
    },
    {
      "anchor": "V82-P2563",
      "ordinal": 2563,
      "style": "BodyCJK",
      "text": "normative_handoff 中的选择记录、C12 闸与 J 授权只能写成规范缺失状态，或写成带 record_type、外部记录 ID、报告状态和独立 verification_ref 的外部核验引用。所有 record_id、verification_ref 和程序 ID 都必须是无首尾空白的外部引用；none、self、self:* 及其大小写或空白变体一律无效。selection:passed、C12:passed、J:authorized 之类字符串自报同样无效；工具只链接和核验外部记录，不在本记录中生成这些状态。"
    },
    {
      "anchor": "V82-P2564",
      "ordinal": 2564,
      "style": "BodyCJK",
      "text": "结果状态要保持可区分：passed 表示该项记录门通过，failed 表示已运行但失败，not_run 表示因前闸或范围限制没有运行；unknown、not_applicable、not_observable 与 withheld_for_protection 仍是四种不同缺失状态。失败不能改写成不适用，保护性隐匿不能改写成不存在。"
    },
    {
      "anchor": "V82-P2565",
      "ordinal": 2565,
      "style": "BodyCJK",
      "text": "运行记录的 authorization_effect 恒为 none。即使规范选择、C12、J 和 O 的外部引用均已存在，本记录也只是核对和移交它们，不自行铸造授权。所有已复核输出必须保留可达申诉与实际撤回/纠正路径；不能撤回的工具结论不得进入高影响难逆用途。"
    },
    {
      "anchor": "V82-P2566",
      "ordinal": 2566,
      "style": "SecH2",
      "text": "13.10　多圈层推演九闸"
    },
    {
      "anchor": "V82-P2567",
      "ordinal": 2567,
      "style": "BodyCJK",
      "text": "七闸是解释与诊断的唯一主流程；当任务明确要求动态推演、条件前瞻或有限选择时，在其基础上展开九闸。九闸不得绕过七闸已经规定的对象、证据、受影响位置、权力、反身性、强判断程序和行动上限。"
    },
    {
      "anchor": "V82-P2568",
      "ordinal": 2568,
      "style": "TableHead",
      "text": "闸"
    },
    {
      "anchor": "V82-P2569",
      "ordinal": 2569,
      "style": "TableHead",
      "text": "核心检查"
    },
    {
      "anchor": "V82-P2570",
      "ordinal": 2570,
      "style": "TableHead",
      "text": "失败输出"
    },
    {
      "anchor": "V82-P2571",
      "ordinal": 2571,
      "style": "TableText",
      "text": "DF1 事实冻结"
    },
    {
      "anchor": "V82-P2572",
      "ordinal": 2572,
      "style": "TableText",
      "text": "事件类型、来源、时间、证据截止和争议"
    },
    {
      "anchor": "V82-P2573",
      "ordinal": 2573,
      "style": "TableText",
      "text": "事实问题清单"
    },
    {
      "anchor": "V82-P2574",
      "ordinal": 2574,
      "style": "TableText",
      "text": "DF2 联合对象"
    },
    {
      "anchor": "V82-P2575",
      "ordinal": 2575,
      "style": "TableText",
      "text": "行动者、圈层、关系、成员与 K"
    },
    {
      "anchor": "V82-P2576",
      "ordinal": 2576,
      "style": "TableText",
      "text": "候选分组或单焦点退回"
    },
    {
      "anchor": "V82-P2577",
      "ordinal": 2577,
      "style": "TableText",
      "text": "DF3 双通道与时钟"
    },
    {
      "anchor": "V82-P2578",
      "ordinal": 2578,
      "style": "TableText",
      "text": "物质/体验—意义、五类时钟、未知"
    },
    {
      "anchor": "V82-P2579",
      "ordinal": 2579,
      "style": "TableText",
      "text": "状态快照，不传播"
    },
    {
      "anchor": "V82-P2580",
      "ordinal": 2580,
      "style": "TableText",
      "text": "DF4 机制传播"
    },
    {
      "anchor": "V82-P2581",
      "ordinal": 2581,
      "style": "TableText",
      "text": "通道、阈值、时延、反馈和级联"
    },
    {
      "anchor": "V82-P2582",
      "ordinal": 2582,
      "style": "TableText",
      "text": "候选机制与区分观察"
    },
    {
      "anchor": "V82-P2583",
      "ordinal": 2583,
      "style": "TableText",
      "text": "DF5 路径分叉"
    },
    {
      "anchor": "V82-P2584",
      "ordinal": 2584,
      "style": "TableText",
      "text": "条件、父子节点、早期与反向信号"
    },
    {
      "anchor": "V82-P2585",
      "ordinal": 2585,
      "style": "TableText",
      "text": "并行路径，不强制排序"
    },
    {
      "anchor": "V82-P2586",
      "ordinal": 2586,
      "style": "TableText",
      "text": "DF6 前瞻登记"
    },
    {
      "anchor": "V82-P2587",
      "ordinal": 2587,
      "style": "TableText",
      "text": "目标、期限、简单基线、校准和回写"
    },
    {
      "anchor": "V82-P2588",
      "ordinal": 2588,
      "style": "TableText",
      "text": "仅情景推演"
    },
    {
      "anchor": "V82-P2589",
      "ordinal": 2589,
      "style": "TableText",
      "text": "DF7 规范选择"
    },
    {
      "anchor": "V82-P2590",
      "ordinal": 2590,
      "style": "TableText",
      "text": "N、PF、受影响者、方案与不行动"
    },
    {
      "anchor": "V82-P2591",
      "ordinal": 2591,
      "style": "TableText",
      "text": "需求清单，不推荐"
    },
    {
      "anchor": "V82-P2592",
      "ordinal": 2592,
      "style": "TableText",
      "text": "DF8 授权与执行"
    },
    {
      "anchor": "V82-P2593",
      "ordinal": 2593,
      "style": "TableText",
      "text": "J、O、责任、停止、回滚和补救"
    },
    {
      "anchor": "V82-P2594",
      "ordinal": 2594,
      "style": "TableText",
      "text": "外部移交，不执行"
    },
    {
      "anchor": "V82-P2595",
      "ordinal": 2595,
      "style": "TableText",
      "text": "DF9 结果回写"
    },
    {
      "anchor": "V82-P2596",
      "ordinal": 2596,
      "style": "TableText",
      "text": "结果、基线比较、偏差、降级和退役"
    },
    {
      "anchor": "V82-P2597",
      "ordinal": 2597,
      "style": "TableText",
      "text": "保留失败并开新版本"
    },
    {
      "anchor": "V82-P2598",
      "ordinal": 2598,
      "style": "BodyCJK",
      "text": "工具在 DF2 可以提出圈层候选，在 DF5 可以提出变量候选，但任何候选都保持 candidate。DF6 未通过时，输出不能使用“将会”“预计命中”等前瞻语气；DF7 或 DF8 未通过时，输出不能给出可执行指令。DF9 不允许覆盖原运行。"
    },
    {
      "anchor": "V82-P2599",
      "ordinal": 2599,
      "style": "SecH2",
      "text": "13.11　AI 在动态运行中的边界"
    },
    {
      "anchor": "V82-P2600",
      "ordinal": 2600,
      "style": "BodyCJK",
      "text": "AI 可以整理材料、发现字段缺口、生成竞争路径、检查合同一致性和计算已登记指标。AI 不能验证现实事件、诊断人格、替当事人披露信息、决定圈层边界、把模拟当事实、选择价值前提或签发授权。对 AI 自动提出的变量，系统必须记录来源为模型候选、最小检验和禁止用途；没有外部证据前不得升级。"
    }
  ],
  "tables": [
    {
      "anchor": "V82-T056",
      "cell_paragraph_ordinals": [
        [
          [
            2355
          ],
          [
            2356
          ],
          [
            2357
          ],
          [
            2358
          ]
        ],
        [
          [
            2359
          ],
          [
            2360
          ],
          [
            2361
          ],
          [
            2362
          ]
        ],
        [
          [
            2363
          ],
          [
            2364
          ],
          [
            2365
          ],
          [
            2366
          ]
        ],
        [
          [
            2367
          ],
          [
            2368
          ],
          [
            2369
          ],
          [
            2370
          ]
        ],
        [
          [
            2371
          ],
          [
            2372
          ],
          [
            2373
          ],
          [
            2374
          ]
        ]
      ],
      "ordinal": 56,
      "paragraph_ordinals": [
        2355,
        2356,
        2357,
        2358,
        2359,
        2360,
        2361,
        2362,
        2363,
        2364,
        2365,
        2366,
        2367,
        2368,
        2369,
        2370,
        2371,
        2372,
        2373,
        2374
      ],
      "rows": [
        [
          "ID",
          "转换",
          "必须得到什么",
          "失败时停在哪里"
        ],
        [
          "IT1",
          "结构变量到可观察信号",
          "对象、尺度、观察位置、时间窗、测量协议和缺失状态明确的信号记录",
          "概念映射或材料缺口"
        ],
        [
          "IT2",
          "可观察信号到证据强度",
          "来源、观察、比较条件、覆盖、反例、替代解释和不确定性分开的证据记录",
          "未分级材料或待检验假设"
        ],
        [
          "IT3",
          "证据强度到判断等级",
          "有命题合同、适用边界、反向条件、证伪条件和撤回条件的判断",
          "候选解释或观察意见"
        ],
        [
          "IT4",
          "判断等级到行动要求与上限",
          "受影响位置、保护底板、禁止动作、停止、申诉、回滚及尚缺 N/J/O/C12 的清单",
          "描述、补证或不行动要求"
        ]
      ]
    },
    {
      "anchor": "V82-T057",
      "cell_paragraph_ordinals": [
        [
          [
            2382
          ],
          [
            2383
          ],
          [
            2384
          ],
          [
            2385
          ]
        ],
        [
          [
            2386
          ],
          [
            2387
          ],
          [
            2388
          ],
          [
            2389
          ]
        ],
        [
          [
            2390
          ],
          [
            2391
          ],
          [
            2392
          ],
          [
            2393
          ]
        ],
        [
          [
            2394
          ],
          [
            2395
          ],
          [
            2396
          ],
          [
            2397
          ]
        ],
        [
          [
            2398
          ],
          [
            2399
          ],
          [
            2400
          ],
          [
            2401
          ]
        ],
        [
          [
            2402
          ],
          [
            2403
          ],
          [
            2404
          ],
          [
            2405
          ]
        ],
        [
          [
            2406
          ],
          [
            2407
          ],
          [
            2408
          ],
          [
            2409
          ]
        ],
        [
          [
            2410
          ],
          [
            2411
          ],
          [
            2412
          ],
          [
            2413
          ]
        ]
      ],
      "ordinal": 57,
      "paragraph_ordinals": [
        2382,
        2383,
        2384,
        2385,
        2386,
        2387,
        2388,
        2389,
        2390,
        2391,
        2392,
        2393,
        2394,
        2395,
        2396,
        2397,
        2398,
        2399,
        2400,
        2401,
        2402,
        2403,
        2404,
        2405,
        2406,
        2407,
        2408,
        2409,
        2410,
        2411,
        2412,
        2413
      ],
      "rows": [
        [
          "ID",
          "闸门",
          "核心问题",
          "未通过时的输出上限"
        ],
        [
          "IG1",
          "有效对象闸",
          "对象、边界、九轴尺度、时间窗与 K 是否支持本次判断？",
          "重新界定对象、尺度未知或对象转换复核"
        ],
        [
          "IG2",
          "证据追踪闸",
          "来源、材料、观察、证据、反例、案例与判断是否分开可回溯？",
          "材料整理、候选问题或待检验假设"
        ],
        [
          "IG3",
          "受影响位置闸",
          "哪些直接、间接、二阶、跨域与跨期位置会改变处境？",
          "补充影响核算；暂停强判断和高影响用途"
        ],
        [
          "IG4",
          "权力与反报复闸",
          "低权力位置能否安全补证、反驳、拒绝、停止和申诉？",
          "不得因沉默作不利推断；降低发布与判断档位"
        ],
        [
          "IG5",
          "中介与反身性闸",
          "指标、平台、AI、公开评价或诊断行为是否改变证据和对象？",
          "高反身性未收束；改写为条件状态转移"
        ],
        [
          "IG6",
          "强判断程序闸",
          "高影响、公开或组织化判断是否完整提交 SJ1-SJ8？",
          "内部假设、开放断言或候选机制；不得形成比较判断"
        ],
        [
          "IG7",
          "行动上限闸",
          "最多只能提出什么要求，哪些动作禁止，何时停止、申诉和回滚？",
          "描述、证据缺口、不行动或继续审议"
        ]
      ]
    },
    {
      "anchor": "V82-T058",
      "cell_paragraph_ordinals": [
        [
          [
            2418
          ],
          [
            2419
          ],
          [
            2420
          ],
          [
            2421
          ]
        ],
        [
          [
            2422
          ],
          [
            2423
          ],
          [
            2424
          ],
          [
            2425
          ]
        ],
        [
          [
            2426
          ],
          [
            2427
          ],
          [
            2428
          ],
          [
            2429
          ]
        ],
        [
          [
            2430
          ],
          [
            2431
          ],
          [
            2432
          ],
          [
            2433
          ]
        ],
        [
          [
            2434
          ],
          [
            2435
          ],
          [
            2436
          ],
          [
            2437
          ]
        ],
        [
          [
            2438
          ],
          [
            2439
          ],
          [
            2440
          ],
          [
            2441
          ]
        ]
      ],
      "ordinal": 58,
      "paragraph_ordinals": [
        2418,
        2419,
        2420,
        2421,
        2422,
        2423,
        2424,
        2425,
        2426,
        2427,
        2428,
        2429,
        2430,
        2431,
        2432,
        2433,
        2434,
        2435,
        2436,
        2437,
        2438,
        2439,
        2440,
        2441
      ],
      "rows": [
        [
          "ID",
          "展开闸",
          "必须展开的材料",
          "对应主闸"
        ],
        [
          "FG1",
          "对象闸",
          "对象、边界、尺度、时间窗",
          "IG1"
        ],
        [
          "FG2",
          "证据闸",
          "信号成本、来源、权重、复核",
          "IG2"
        ],
        [
          "FG3",
          "尺度闸",
          "九轴尺度、尺度内对象与证据、尺度变化",
          "IG1、IG2"
        ],
        [
          "FG4",
          "责任闸",
          "权利/资源影响、反向条件、修复窗口、申诉复核",
          "IG3、IG4、IG6"
        ],
        [
          "FG5",
          "观测闸",
          "观察前基线、观察中反应、发布后反应、递归封顶",
          "IG5"
        ]
      ]
    },
    {
      "anchor": "V82-T059",
      "cell_paragraph_ordinals": [
        [
          [
            2443
          ],
          [
            2444
          ],
          [
            2445
          ]
        ],
        [
          [
            2446
          ],
          [
            2447
          ],
          [
            2448
          ]
        ],
        [
          [
            2449
          ],
          [
            2450
          ],
          [
            2451
          ]
        ],
        [
          [
            2452
          ],
          [
            2453
          ],
          [
            2454
          ]
        ],
        [
          [
            2455
          ],
          [
            2456
          ],
          [
            2457
          ]
        ],
        [
          [
            2458
          ],
          [
            2459
          ],
          [
            2460
          ]
        ],
        [
          [
            2461
          ],
          [
            2462
          ],
          [
            2463
          ]
        ],
        [
          [
            2464
          ],
          [
            2465
          ],
          [
            2466
          ]
        ],
        [
          [
            2467
          ],
          [
            2468
          ],
          [
            2469
          ]
        ],
        [
          [
            2470
          ],
          [
            2471
          ],
          [
            2472
          ]
        ],
        [
          [
            2473
          ],
          [
            2474
          ],
          [
            2475
          ]
        ],
        [
          [
            2476
          ],
          [
            2477
          ],
          [
            2478
          ]
        ],
        [
          [
            2479
          ],
          [
            2480
          ],
          [
            2481
          ]
        ],
        [
          [
            2482
          ],
          [
            2483
          ],
          [
            2484
          ]
        ]
      ],
      "ordinal": 59,
      "paragraph_ordinals": [
        2443,
        2444,
        2445,
        2446,
        2447,
        2448,
        2449,
        2450,
        2451,
        2452,
        2453,
        2454,
        2455,
        2456,
        2457,
        2458,
        2459,
        2460,
        2461,
        2462,
        2463,
        2464,
        2465,
        2466,
        2467,
        2468,
        2469,
        2470,
        2471,
        2472,
        2473,
        2474,
        2475,
        2476,
        2477,
        2478,
        2479,
        2480,
        2481,
        2482,
        2483,
        2484
      ],
      "rows": [
        [
          "ID",
          "步骤",
          "最小产物"
        ],
        [
          "DS01",
          "问题入口",
          "不使用框架术语的现实问题、请求者和用途"
        ],
        [
          "DS02",
          "对象与边界",
          "有效对象、子系统、上级环境和外部通道"
        ],
        [
          "DS03",
          "信号分层",
          "事实、行为、资源、反馈、叙事、感受、推测和噪声分栏"
        ],
        [
          "DS04",
          "观测参与登记",
          "被观察知情、观察者权力、发布影响和候选反应"
        ],
        [
          "DS05",
          "主导约束",
          "候选约束、所选约束、选择证据和竞争约束"
        ],
        [
          "DS06",
          "状态与窗口",
          "S0-S6 原型引用、状态内位置、并行子系统和反向条件"
        ],
        [
          "DS07",
          "核心结构扫描",
          "锚点、承接层、传导链、边界和反馈写回"
        ],
        [
          "DS08",
          "关键保护变量",
          "受保护变量、受损路径、资源、冗余和修复/回流路径"
        ],
        [
          "DS09",
          "承接与偿付",
          "成本承担者、回流获得者、停止权、长期透支与损害转移"
        ],
        [
          "DS10",
          "隐患与边界类型",
          "维护债、快慢错配、指标替代、摘要失真和对象转换候选"
        ],
        [
          "DS11",
          "机制候选",
          "至少两个竞争机制、各自所需证据、削弱证据和淘汰规则"
        ],
        [
          "DS12",
          "分支预判",
          "触发、早期信号、反向条件、修复窗口和最低行动要求"
        ],
        [
          "DS13",
          "输出与写回",
          "现实语言输出、修改触发器、记录范围、复核、撤回和回滚"
        ]
      ]
    },
    {
      "anchor": "V82-T060",
      "cell_paragraph_ordinals": [
        [
          [
            2488
          ],
          [
            2489
          ],
          [
            2490
          ]
        ],
        [
          [
            2491
          ],
          [
            2492
          ],
          [
            2493
          ]
        ],
        [
          [
            2494
          ],
          [
            2495
          ],
          [
            2496
          ]
        ],
        [
          [
            2497
          ],
          [
            2498
          ],
          [
            2499
          ]
        ],
        [
          [
            2500
          ],
          [
            2501
          ],
          [
            2502
          ]
        ],
        [
          [
            2503
          ],
          [
            2504
          ],
          [
            2505
          ]
        ],
        [
          [
            2506
          ],
          [
            2507
          ],
          [
            2508
          ]
        ],
        [
          [
            2509
          ],
          [
            2510
          ],
          [
            2511
          ]
        ],
        [
          [
            2512
          ],
          [
            2513
          ],
          [
            2514
          ]
        ]
      ],
      "ordinal": 60,
      "paragraph_ordinals": [
        2488,
        2489,
        2490,
        2491,
        2492,
        2493,
        2494,
        2495,
        2496,
        2497,
        2498,
        2499,
        2500,
        2501,
        2502,
        2503,
        2504,
        2505,
        2506,
        2507,
        2508,
        2509,
        2510,
        2511,
        2512,
        2513,
        2514
      ],
      "rows": [
        [
          "ID",
          "组件",
          "必须回答什么"
        ],
        [
          "SJ1",
          "反向条件",
          "出现什么情况会削弱、反转或撤回判断？"
        ],
        [
          "SJ2",
          "修复窗口",
          "窗口何在、根据何在、何时失效？"
        ],
        [
          "SJ3",
          "证据要求",
          "支持、缺失和反向证据分别是什么？"
        ],
        [
          "SJ4",
          "申诉入口",
          "谁可进入、谁负责、时限多长、能否改变结果？"
        ],
        [
          "SJ5",
          "反报复保护",
          "哪些行为受保护、如何监测、如何独立报告和补救？"
        ],
        [
          "SJ6",
          "证据补充权",
          "如何补证、纠正版本并同步下游？"
        ],
        [
          "SJ7",
          "外部复核触发",
          "何时触发、谁独立复核、能否访问材料和停止结果？"
        ],
        [
          "SJ8",
          "回滚与写回",
          "回到哪个状态、谁修复、哪个版本权威、如何同步？"
        ]
      ]
    },
    {
      "anchor": "V82-T061",
      "cell_paragraph_ordinals": [
        [
          [
            2517
          ],
          [
            2518
          ],
          [
            2519
          ],
          [
            2520
          ]
        ],
        [
          [
            2521
          ],
          [
            2522
          ],
          [
            2523
          ],
          [
            2524
          ]
        ],
        [
          [
            2525
          ],
          [
            2526
          ],
          [
            2527
          ],
          [
            2528
          ]
        ],
        [
          [
            2529
          ],
          [
            2530
          ],
          [
            2531
          ],
          [
            2532
          ]
        ]
      ],
      "ordinal": 61,
      "paragraph_ordinals": [
        2517,
        2518,
        2519,
        2520,
        2521,
        2522,
        2523,
        2524,
        2525,
        2526,
        2527,
        2528,
        2529,
        2530,
        2531,
        2532
      ],
      "rows": [
        [
          "ID",
          "档位",
          "适用",
          "输出上限"
        ],
        [
          "L1",
          "轻量描述与试探问题",
          "低复杂、低影响、可逆且信息有限",
          "描述、问题和下一观察"
        ],
        [
          "L2",
          "标准可复核判断",
          "需要结构比较但不进入高责任处置",
          "有边界的比较判断或机制候选"
        ],
        [
          "L3",
          "高责任强判断候选",
          "高影响、公开、自动化、组织化、制度化或高权力密度",
          "七闸与八件套通过后的强判断候选"
        ]
      ]
    },
    {
      "anchor": "V82-T062",
      "cell_paragraph_ordinals": [
        [
          [
            2535
          ],
          [
            2536
          ],
          [
            2537
          ]
        ],
        [
          [
            2538
          ],
          [
            2539
          ],
          [
            2540
          ]
        ],
        [
          [
            2541
          ],
          [
            2542
          ],
          [
            2543
          ]
        ],
        [
          [
            2544
          ],
          [
            2545
          ],
          [
            2546
          ]
        ],
        [
          [
            2547
          ],
          [
            2548
          ],
          [
            2549
          ]
        ],
        [
          [
            2550
          ],
          [
            2551
          ],
          [
            2552
          ]
        ],
        [
          [
            2553
          ],
          [
            2554
          ],
          [
            2555
          ]
        ]
      ],
      "ordinal": 62,
      "paragraph_ordinals": [
        2535,
        2536,
        2537,
        2538,
        2539,
        2540,
        2541,
        2542,
        2543,
        2544,
        2545,
        2546,
        2547,
        2548,
        2549,
        2550,
        2551,
        2552,
        2553,
        2554,
        2555
      ],
      "rows": [
        [
          "ID",
          "工具",
          "作用与边界"
        ],
        [
          "TOOL-EVIDENCE-LEDGER",
          "来源—证据台账",
          "分离来源、材料、观察、证据、反例、覆盖和不确定性；不证明命题"
        ],
        [
          "TOOL-OPEN-ASSERTION",
          "开放断言记录",
          "留下可质疑、可证伪、可撤回的临时判断靶点；不用作高责任处置"
        ],
        [
          "TOOL-CLAIM-VALIDATION",
          "命题验证表",
          "对命题类型、证据、反证、证伪条件、影响与上限逐项登记"
        ],
        [
          "TOOL-FORECAST-REGISTRY",
          "前瞻登记",
          "冻结预测、窗口、触发、早期信号、反向信号和修改目标"
        ],
        [
          "TOOL-STRESS-TEST",
          "反例与尺度压力测试",
          "用边界案例、对抗解释和尺度变化找失败位置并收缩范围"
        ],
        [
          "TOOL-AI-BOUNDARY",
          "AI 输出边界",
          "强制来源披露、缺失材料、人类责任人、不确定性、禁止用途和复核撤回"
        ]
      ]
    },
    {
      "anchor": "V82-T063",
      "cell_paragraph_ordinals": [
        [
          [
            2568
          ],
          [
            2569
          ],
          [
            2570
          ]
        ],
        [
          [
            2571
          ],
          [
            2572
          ],
          [
            2573
          ]
        ],
        [
          [
            2574
          ],
          [
            2575
          ],
          [
            2576
          ]
        ],
        [
          [
            2577
          ],
          [
            2578
          ],
          [
            2579
          ]
        ],
        [
          [
            2580
          ],
          [
            2581
          ],
          [
            2582
          ]
        ],
        [
          [
            2583
          ],
          [
            2584
          ],
          [
            2585
          ]
        ],
        [
          [
            2586
          ],
          [
            2587
          ],
          [
            2588
          ]
        ],
        [
          [
            2589
          ],
          [
            2590
          ],
          [
            2591
          ]
        ],
        [
          [
            2592
          ],
          [
            2593
          ],
          [
            2594
          ]
        ],
        [
          [
            2595
          ],
          [
            2596
          ],
          [
            2597
          ]
        ]
      ],
      "ordinal": 63,
      "paragraph_ordinals": [
        2568,
        2569,
        2570,
        2571,
        2572,
        2573,
        2574,
        2575,
        2576,
        2577,
        2578,
        2579,
        2580,
        2581,
        2582,
        2583,
        2584,
        2585,
        2586,
        2587,
        2588,
        2589,
        2590,
        2591,
        2592,
        2593,
        2594,
        2595,
        2596,
        2597
      ],
      "rows": [
        [
          "闸",
          "核心检查",
          "失败输出"
        ],
        [
          "DF1 事实冻结",
          "事件类型、来源、时间、证据截止和争议",
          "事实问题清单"
        ],
        [
          "DF2 联合对象",
          "行动者、圈层、关系、成员与 K",
          "候选分组或单焦点退回"
        ],
        [
          "DF3 双通道与时钟",
          "物质/体验—意义、五类时钟、未知",
          "状态快照，不传播"
        ],
        [
          "DF4 机制传播",
          "通道、阈值、时延、反馈和级联",
          "候选机制与区分观察"
        ],
        [
          "DF5 路径分叉",
          "条件、父子节点、早期与反向信号",
          "并行路径，不强制排序"
        ],
        [
          "DF6 前瞻登记",
          "目标、期限、简单基线、校准和回写",
          "仅情景推演"
        ],
        [
          "DF7 规范选择",
          "N、PF、受影响者、方案与不行动",
          "需求清单，不推荐"
        ],
        [
          "DF8 授权与执行",
          "J、O、责任、停止、回滚和补救",
          "外部移交，不执行"
        ],
        [
          "DF9 结果回写",
          "结果、基线比较、偏差、降级和退役",
          "保留失败并开新版本"
        ]
      ]
    }
  ]
}
```
<!-- canonical-records:end -->
