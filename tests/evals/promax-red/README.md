# CrossFrame ProMax RED baselines

## Method

This fixture freezes twelve actual no-ProMax answers before the ProMax runtime exists. The prompts, evaluator conditions, pressure tags, and raw response paths are indexed by `scenarios.json`; the full requests, turn identities, fork status, thread-limit feedback, and response mapping are frozen in [transcript.json](transcript.json). Each response is preserved without post-hoc rewriting under `raw/`. The `## SCENARIO ...` heading in every raw file was part of the original final response and is therefore retained.

One fresh-fork no-skill evaluator answered A1-A3 together; CrossFrame ProMax was not loaded, and the v8 DOCX was consulted read-only as needed. A requested fresh evaluator for B could not be created because the platform returned `agent thread limit reached`. B, C, and D therefore ran in later separate turns of that same no-skill evaluator. D was not a fresh fork. This limitation is recorded rather than describing any B, C, or D scenario as independently fresh.

Prompt provenance is literal. A1-A3 and D1 store the actual standalone prompts verbatim. B1-B4 and C1-C4 store the exact compressed scenario clauses extracted from combined instructions, rather than reconstructed full prompts. Some raw answers nevertheless supplied facts that those compressed clauses did not provide—for example, B1 introduced three departures in one month, B2 introduced a newly launched algorithm, and B4 introduced a one-neighborhood traffic pilot. Those evaluator-added facts are observable RED behavior, not prompt content or verified evidence.

Safety-preserving judgments are not counted as failures. Several baseline answers correctly rejected unsupported causality, personality diagnosis, selective retrieval, scale leakage, fabricated search, or prediction-derived authorization. Their RED status comes from the absence of the future ProMax execution contract, not from treating those safe conclusions as wrong.

The observable ProMax gaps are the absence of a frozen v8 anchor and read-event trail; concept terminal closure; typed claim-path coverage; a retrieval ledger; red-team saturation; typed example coverage; position and recommendation ledgers; continuation state; artifact validation; validator evidence; and repair-loop closure. C4 is the substantive routing exception: it explicitly permits and proposes Max fallback after ProMax was named, which conflicts with the new no-fallback specification.

## Per-scenario observable gaps

| Scenario | Observable baseline gap |
| --- | --- |
| A1 | Safe rejection of an absolute causal claim, but no v8 anchor/read-event ledger, concept terminal closure, typed claim-path set, or artifact validation. |
| A2 | Safe rejection of an absolute zero-risk claim, but no v8 anchor/read-event ledger, concept terminal closure, typed claim-path set, or artifact validation. |
| A3 | Safe rejection of personality and dismissal leaps, but no typed example artifact, judgment-charter trace, red-team saturation record, or validator result. |
| B1 | Safe material-insufficiency judgment, but the answer invented three departures and a one-month window absent from the compressed prompt; it also lacks a source/read ledger, terminal concept closure, typed competing claim paths, or repair artifact. |
| B2 | Safe refusal to equate jargon with completeness, but the answer invented a newly launched algorithm absent from the compressed prompt and lacks auditable concept terminal closure, typed examples, or artifact validation. |
| B3 | Safe refusal of support-only evidence selection, but no executed retrieval ledger, saturation status, source coverage artifact, or validator result. |
| B4 | Safe separation of local evidence, forecast, and authorization, but the answer invented a one-neighborhood traffic pilot absent from the compressed prompt and lacks a scale claim-path artifact, position ledger, recommendation ledger, or validation. |
| C1 | Safe candidate-object downgrade, but no v8 object anchor, read-event trail, terminal concept closure, or calibrated continuation ledger. |
| C2 | Safe refusal to apply S0-S6 to an individual, but no typed misuse example artifact, claim-path trace, or validator evidence. |
| C3 | Safe refusal to fabricate exhaustive retrieval, but no retrieval ledger or explicit saturation state because the tools were unavailable. |
| C4 | Actual routing conflict: the answer allows and proposes Max fallback after ProMax is named; the target contract requires ProMax priority and no Max fallback. |
| D1 | Safe refusal to issue `promax-complete`, but no ProMax artifact contract, validator execution, repair loop, or validated completion state. |

## Commands

Target RED suite:

```powershell
python -B -m unittest tests.test_promax_behavioral_contract tests.test_promax_repository_integration -v
```

Existing regression suite:

```powershell
python -B -m unittest tests.test_mirror_integrity tests.test_verify_workflow_contract -v
```

## RED result summary

Observed after the provenance and contract hardening:

```text
Ran 16 tests
FAILED (failures=10; errors=0)
```

There were no import, syntax, fixture, or runtime errors. Eight checks passed: all four frozen-baseline and transcript checks, both Git-authoritative Max preservation checks, the generic maximum-request routing check, and the named-Max identity check. The ten expected assertion failures were:

- four behavioral-contract assertions stopped at the missing canonical skill or its specifically assigned protocol file;
- inventory reported `expected 16 CrossFrame skills, got 15`;
- the canonical ProMax skill and Claude command were absent;
- the exact bounded routing-contract assertion failed independently for `SKILL.md`, `suite-dispatch-protocol.md`, and `workflow-routing-map.md` because none yet contains its single `PROMAX-ROUTING-BEGIN` / `PROMAX-ROUTING-END` block.

This is the intended RED state: the captured controls and Max preservation manifest are valid, while only the not-yet-implemented ProMax production contracts fail.

The existing regression command remained green:

```text
Ran 3 tests
OK
```
