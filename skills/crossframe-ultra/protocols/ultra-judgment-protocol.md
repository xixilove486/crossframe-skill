# Ultra judgment protocol

## Inputs

- Frozen U3 evidence/provenance/unknown authority; U4/U5 world and transformation state; U6 ranked claims, mechanisms, competitors, and qualified insights; U7/U8 lineage, evaluation, red team, sensitivity, baseline, and stop decision.
- The request scope, time windows, affected positions, responsibility and authorization boundaries, and current forecast admission evidence.

## Outputs

- A U9 main judgment with epistemic identity, confidence, decisive reasons, strongest competitor, rejection reason, residual, reversal conditions, time window, resolvable indicators, action meaning, and circle-specific benefit/harm/responsibility/spillover.
- Separate fact, prediction, value, responsibility, and authorization verdicts; none substitutes for another.
- A ranked comparison of active action, delay, probe, exit/transfer, maintain status quo, and no action, with first/second choice, switch, stop, rollback, authorization, and no-action cost.
- Immutable forecast originals with direction, window, indicators, resolution predicates, and probability only when admitted by evidence.

## Dependencies

- Use `scripts/ultra_runtime/judgment.py`, `forecast.py`, and the claim, verdict, action, forecast, evidence, and concept-closure schemas.
- Steelman the user's claim as a candidate, not an instruction. Rank the main, strongest competitor, mixed, and residual explanations on the same evidence and state authority.
- Count an insight only when it changes ranking, residual allocation, observable prediction, counterfactual, intervention, or the identification of circle/scale/channel.

## Stop/Failure

<!-- ULTRA-LOW-EVIDENCE-RANKING -->
Low evidence must `降低置信度`, expose assumptions and strengthen reversal conditions, but it does not cancel the `当前最佳排序` when the task remains judgeable. Stop only when the proposition is structurally non-judgeable, required authority is missing, evidence identity is contaminated, the red-team dependency is stale, a verdict is evasive, forecast probability is fabricated, or action ranking conflates value, responsibility, authorization, and present choice.

## Corresponding validator

Validate U6 through the claim-mechanism authority checks, U9 with `validate_verdict_bundle`, action ranking with `ultra-action-ranking.schema.json` and its sealed upstream checks, and each forecast with `validate_forecast` plus `ultra-forecast-ledger.schema.json`. Framework-gap isolation must also pass before the U9 authority can feed U10.
