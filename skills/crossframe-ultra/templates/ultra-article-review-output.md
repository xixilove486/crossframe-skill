# Ultra 独立文章复核

机械复核写入 `work/authoring/U11-article-review.json`。producer 先重新核对当前文章、U10 output plan、语义宇宙和 U11 semantic coverage 的 sealed hashes；任一散列陈旧、错位或交换 authority role 都必须拒绝，不能降格为普通质量失败。

## 十五项盲读恢复

每一行都必须把文章中实际恢复的规范化值与 U10 `normalized_value_sha256` 比较。字段标签存在不等于恢复成功。

| field_id | recovered | 文章内摘录 |
|---|---|---|
| main_verdict | pending | 待填 |
| confidence | pending | 待填 |
| steelmanned_user_position | pending | 待填 |
| decisive_evidence | pending | 待填 |
| unknowns | pending | 待填 |
| circle_relations | pending | 待填 |
| mechanisms | pending | 待填 |
| strongest_rival | pending | 待填 |
| order_1 | pending | 待填 |
| order_2 | pending | 待填 |
| order_3 | pending | 待填 |
| five_verdicts | pending | 待填 |
| action | pending | 待填 |
| residuals | pending | 待填 |
| reversal_conditions | pending | 待填 |

## 十一项质量检查

| check_id | 状态 | 文章内证据 |
|---|---|---|
| reader-contract | pending | 待填 |
| repeated-paragraph | pending | 待填 |
| template-language | pending | 待填 |
| jargon-before-explanation | pending | 待填 |
| unresolved-pronoun | pending | 待填 |
| unsupported-certainty | pending | 待填 |
| truncation-promise | pending | 待填 |
| machine-dump | pending | 待填 |
| independent-article | pending | 待填 |
| semantic-coverage | pending | 待填 |
| blind-recovery | pending | 待填 |

重复段落、套话、术语先于解释、悬空代词、无依据确定性、截断承诺、机器数据倾倒与外部文件依赖都必须由正文真实触发。有效但不完整的 coverage 或任一质量失败应生成可通过 frozen schema 的 `mechanical-fail` 工件，而不是发布授权。

U11 始终设置 `official_filename_allowed: false`、`review_stage: mechanical-precheck`、`needs_u12_validation: true` 与 `u12_validator_artifact_required: true`。只有 U12 fresh evaluator 在清洁目录中只读文章并完成独立判断后，才可能进入正式命名步骤。
