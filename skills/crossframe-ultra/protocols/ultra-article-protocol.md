# Ultra article protocol

## Inputs

- The locked U9 judgment, five verdicts, action ranking, forecast originals, reversal conditions, circle-specific distributions, and all substantive upstream semantic units that affected ranking.
- The U10 framework-gap isolation ledger and output plan; U11 article packets, semantic-coverage map, dossier, mechanical article-review slot, and accepted persistent semantic-review host receipt.
- Task 11 article templates and, after integration, Task 13 dossier/index/publication templates.

## Outputs

- One continuous independently readable Chinese article covering the main judgment, steelmanned user position, facts/provenance/unknowns, world volume, mechanisms/channels/cascades, competitor ranking, orders 1–3, per-order baseline/increment/stop, five verdicts, actions, switch and reversal conditions.
- In the same article, appendices for circle-role-scale mapping, branch/merge/prune/residual/stop points, forecast windows/indicators/resolution, concept/evidence/source anchors, unknowns, and isolated framework-gap candidates.
- A 100% semantic-coverage artifact, blind-reader field recovery, mechanical clean-room article review, separately attested fresh semantic review, complete dossier, partial article before U12, and official article only after U12.

## Dependencies

- Use `scripts/ultra_runtime/article.py`, `coverage.py`, and `semantic_review.py`; follow `ultra-output-plan-output.md`, `ultra-article-output.md`, `ultra-semantic-coverage-output.md`, and `ultra-article-review-output.md` without inventing template fields.
- Assemble frozen packets deterministically when context is limited. Keep every conclusion-affecting unit visible in a concrete article section/paragraph; internal files may add audit detail but cannot carry a hidden premise needed to understand the judgment.
- Keep the U11 mechanical review limited to packet structure, ID coverage, blind-reader recovery, duplicate prose, and machine-dump checks. The runtime issues the fresh semantic review as a persistent host action bound to the current request/intake, active U10 parent and generation, article, output plan, coverage, article review, evidence, concept disposition, and required concept semantic units. The host supplies only reviewer identity and nine dimension judgments; the runtime owns the semantic artifact envelope and publication disposition, and semantic review cannot override a deterministic or adversarial failure.
- Preserve source identity and translate only concepts that change the judgment. Do not expose hidden chain-of-thought, tool traces, or machine dumps.

## Stop/Failure

<!-- ULTRA-NO-WORD-CAP -->
There is no word cap; finish on semantic closure and readability, not length. <!-- ULTRA-BLIND-RECOVERY-GATE --> Do not mark the article complete before a clean reader can recover every locked judgment field without the dossier. Stop on missing coverage, dependency leakage, machine-record prose, unordered packets, changed locked judgment, fabricated quotation, unresolved substantive residual, or insufficient capacity to finish assembly; retain a partial filename and incomplete status.

## Corresponding validator

Run `validate_output_plan_artifact`, packet authority checks, article assembly validation, `validate_semantic_coverage`, `validate_frozen_blind_recovery_contract`, `review_article_in_clean_room`, and `validate_semantic_review`. Validate the resulting artifacts with the output-plan, semantic-coverage, article-review, and semantic-review schemas. Publication requires deterministic, adversarial, and fresh-semantic validator layers to pass for the same article and manifest generation.
