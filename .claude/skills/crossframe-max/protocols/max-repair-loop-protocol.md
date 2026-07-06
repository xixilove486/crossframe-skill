# Max Repair Loop Protocol

## 0. 目标

validator 不是终点，而是状态转换器。validator failed 后必须进入 repair loop，而不是整轮重抽或直接改写最终正文。

## 1. 核心链路

```text
generate artifacts
-> run validators
-> max-validator-report.json
-> classify errors
-> max-repair-plan.json
-> affected phase reset
-> regenerate downstream
-> revalidate
-> pass / downgrade / withdraw / max-incomplete
```

## 2. 禁止

- 禁止 validator failed 后直接重写 final essay。
- 禁止为了过 marker 检查堆 marker。
- 禁止伪造 source_anchor、claim_id、source_paragraph_ids。
- 禁止把 evidence insufficient 改写成 evidence supported。
- 禁止绕过 phase lock 直接 patch 下游 Markdown。

## 3. Phase Map

```text
phase: run_contract
artifact: max-run-contract.json
downstream: all

phase: read_plan
artifact: max-read-plan.json
downstream:
  - max-source-snapshot.json
  - max-worldview-capsule.locked.md
  - max-local-world-model.locked.md
  - max-concept-hit-ledger.json
  - max-claim-board.json
  - max-audit-board.json
  - max-output-plan.locked.md
  - max-dossier.md
  - max-essay.md

phase: source_snapshot
artifact: max-source-snapshot.json
downstream:
  - max-worldview-capsule.locked.md
  - max-local-world-model.locked.md
  - max-concept-hit-ledger.json
  - max-claim-ledger.json
  - max-evidence-reasoning-audit.json
  - max-output-plan.locked.md
  - max-dossier.md
  - max-essay.md

phase: concept_hit
artifact:
  - max-concept-hit-ledger.json
  - max-concept-graph section in max-dossier.md
downstream:
  - max-claim-ledger.json
  - max-claim-board.json
  - max-evidence-reasoning-audit.json
  - max-audit-board.json
  - max-output-plan.locked.md
  - max-dossier.md
  - max-essay.md

phase: claim
artifact:
  - max-claim-ledger.json
  - max-claim-board.json
downstream:
  - max-evidence-reasoning-audit.json
  - max-audit-board.json
  - max-output-plan.locked.md
  - max-dossier.md
  - max-essay.md

phase: audit
artifact:
  - max-evidence-reasoning-audit.json
  - max-audit-board.json
downstream:
  - max-output-plan.locked.md
  - max-dossier.md
  - max-essay.md

phase: output_plan
artifact: max-output-plan.locked.md
downstream:
  - max-dossier.md
  - max-essay.md
  - max-continuation-ledger.md
  - max-continuation-index.md

phase: final_markdown
artifact:
  - max-dossier.md
  - max-essay.md
  - max-continuation-ledger.md
  - max-continuation-index.md
downstream: []
```

## 4. Error Taxonomy

```text
missing_artifact
invalid_json
route_registry_closure_failed
route_plan_mismatch
concept_registry_missing
concept_source_anchor_mismatch
concept_contract_missing
source_paragraph_not_in_read_range
claim_missing_audit
claim_missing_concept_hit
evidence_chain_missing
counterevidence_missing
external_search_required
essay_too_short
dossier_section_too_thin
repeated_filler
forbidden_output_present
missing_claim_or_source_reference
full_source_incomplete
unrepairable_repository_state
retry_budget_exhausted
```

## 5. Repair Action

```text
repair_action: create_missing_artifact
repair_action: regenerate_markdown_only
repair_action: regenerate_concept_hit_and_downstream
repair_action: regenerate_claim_and_downstream
repair_action: regenerate_audit_and_downstream
repair_action: regenerate_output_plan_and_final_markdown
repair_action: downgrade_claim
repair_action: withdraw_claim
repair_action: needs_external_search
repair_action: repository_maintenance_required
repair_action: max_incomplete
```

## 6. Retry Policy

```text
default max_retry_count: 2
hard max_retry_count: 3
```

超过 retry budget 后必须输出 `max-incomplete: validation-retry-budget-exhausted`。

## 7. 证据不足规则

证据不足不是自动重生成理由。如果错误类型是 `evidence_chain_missing`、`counterevidence_missing`、`external_search_required` 或 `source_anchor_not_found`，repair action 优先是 `downgrade_claim`、`withdraw_claim` 或 `max_incomplete`，不是补写强判断。
