# Case and countercase 生成合同

产物：`promax-case-and-countercase.md`
生成阶段：`P10`
冻结输入：claim/path graph、retrieval ledger、output plan

顶层只使用 `# ProMax v8 案例与反例`。每条案例必须使用一个二级标题，且所有 `##` 标题都严格符合：

```text
## EXAMPLE-ID | mechanism=MECH-ID | relation=similar|failure | type=real_case|user_material|conditional_scenario|structural_analogy
```

实际标题只能选择一个 `relation` 和一个 `type`，不能保留竖线右侧的多选写法。`EXAMPLE-ID` 必须与 locked output plan 对应集合完全相等，`MECH-ID` 必须存在于 claim graph。

## 数量与类型硬门

- 每个机制至少两个 `relation=similar` 案例和一个 `relation=failure` 案例。
- `type` 只能是 `real_case`、`user_material`、`conditional_scenario`、`structural_analogy`。
- `real_case` 必须链接 retrieval ledger 中可回查来源；没有来源就不能使用该类型。
- `user_material` 只能证明用户材料实际提供的内容。
- `conditional_scenario` 必须使用明确的若—则条件。
- `structural_analogy` 只声明关系相似，不把对象、事实或结果说成相同。

## Similar 案例正文

每条正文必须同时出现：

1. 对应机制的精确 `label`；
2. 该机制至少一个精确 `distinguishing_conditions`；
3. “相似”“类比”“条件”或“因为”等显式关系词；
4. 对象、尺度、时间窗、触发、结果与相似范围；
5. 不相似之处和不能由案例证明的结论。

不得只把机制 label 与条件复制到一行。必须解释为何该条件使案例具有区分力，以及什么观察会转向竞争机制。

## Failure 案例正文

每条正文必须同时出现对应机制的精确 `label`、至少一个机制区分条件，以及“失效”“反例”“不成立”“停止”或“退出”等显式失败词。说明失败发生在哪个前提、信号、尺度变换或结果写回，并写出它是否改变中心判断、路径排序或撤回条件。

## 真实来源纪律

真实案例列出 URL、标题、发布者、事件日期、来源类型和 independence group，并说明来源 `cannot_prove`。重复或衍生来源不能作为独立案例计数。外部案例只能压力测试 v8 推演，不能改写 canonical concept 定义。

案例正文完成后，检查 similar IDs 与 output plan 的 `example_ids` 精确相等，failure IDs 与 `counterexample_ids` 精确相等；任何额外 `##` 标题都会使解析失败。
