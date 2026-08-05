# Ultra 文章语义覆盖审计

审计工件写入 `work/authoring/U11-semantic-coverage.json`。审计对象是最终组装文本中的真实读者语言，不是标题、占位符、概念名堆叠或内部档案。凡被应用、保留、尚未解决、参与推理、影响排序或承诺向读者交代的实质单元，都必须落到一个准确章节和一段可在正文中找到的规范化摘录。

| 单元标识 | 单元种类 | 状态或作用 | 章节标识 | 正文规范化摘录 | 来源锚点 | 验证结果 |
|---|---|---|---|---|---|---|
| 待填 | claim / evidence / unknown / circle-relation / scale-transform / translation-loss / mechanism / branch / residual / forecast / verdict / action / reversal-condition | 待填 | 待填 | 待填 | 待填 | pending |

验证顺序：先核对 U10 output-plan sealed hash、语义宇宙散列与文章散列，再核对 `unit_id` 属于对应 frozen `section.semantic_unit_ids`，随后核对摘录已规范化、在该章节正文中唯一真实出现且映射遵循文章顺序，最后核对所有必需单元均已覆盖。每个 mapping 的 `source_refs` 必须非空并与对应 semantic-universe unit 的 frozen `source_refs` 一致，不能任意替换。任何参与结论排序却只存在于档案中的单元都使审计失败。

若映射尚缺失，producer 仍生成可通过 frozen schema 的 controlled-incomplete 工件，明确列出 `missing_unit_ids`、低于 100 的 `coverage_percent` 与 `coverage_complete: false`；该状态不能发布，也不能伪装为完整覆盖。

覆盖审计只验证可机械定位的文本合同，不能把标题、标签、空泛句或字段非空误当成具体论证。十五项盲读字段还必须排除占位与重复样板；论证是否真正公平、充分和有洞见，留给不参与生成的 fresh evaluator 在只保留文章的清洁目录中独立判断。
