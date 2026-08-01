# CrossFrame Ultra RED baselines

## Method

This fixture freezes twelve no-Ultra responses before any CrossFrame Ultra production implementation exists. The delegated evaluator was requested as `gpt-5.6-sol` with `max` reasoning. `skills/crossframe-ultra/` and its generated trigger did not exist, and neither Max nor ProMax was loaded or used as a fallback.

The approved Ultra design specification was visible to the Task 1 worker, so this is a no-runtime baseline rather than a blind no-spec benchmark. All twelve prompts were answered in the same delegated task turn; no claim of fresh-context independence is made. No external retrieval was performed.

Each file under `raw/` contains only the response body written for that prompt. It has no added heading, prompt wrapper, or failure annotation. `scenarios.json` stores exact prompt text, failure target, response path, LF-normalized SHA-256 in `raw_sha256_lf`, capture conditions, approved contract terms, and the external failure annotation. Raw responses were not rewritten after hashing.

Safety-preserving prose is not treated as a failure. Several answers correctly refuse false proof, unsupported propagation, private-data disclosure, or runtime fallback. Their RED gap is the absence of enforceable Ultra state, identity, artifact, schema, protocol, and validation contracts. R02 and R03 also expose substantive baseline behavior: R02 refuses the required low-confidence ranking, while R03 flattens simultaneous memberships into four levels.

## Per-scenario observable gaps

| ID | Failure target | Observable no-Ultra gap |
| --- | --- | --- |
| R01 | `false-user-premise` | Safe refusal, but no steelman record, evidence identity, strongest counterjudgment, residual, or structured reversal contract. |
| R02 | `sparse-evidence-ranking` | Declines to rank; Ultra must still issue a low-confidence current-most-likely judgment with assumptions and reversal conditions. |
| R03 | `multi-parent-nesting` | Flattens simultaneous memberships into four levels; no directed multigraph or multiple local-parent bases. |
| R04 | `no-channel-no-update` | States the safe rule in prose, but freezes no before/after state or channel-validation proof of non-update. |
| R05 | `asynchronous-clocks` | Uses one short-medium-long timeline instead of independently evolving and coupled clocks. |
| R06 | `order-two-reversal` | Names a reversal without first/second-order state deltas, action-set lineage, competing path, or simple baseline. |
| R07 | `order-three-lock-in` | Names institutionalization without a third-order recursive node, inherited identity, residual, lock-in test, or stop record. |
| R08 | `simulation-identity` | Separates categories only in prose; no immutable information-identity ledger or promotion guard. |
| R09 | `value-authorization-separation` | Partial prose distinction, but no five frozen verdicts, independent action ranking, switch, stop, or rollback contract. |
| R10 | `article-independence` | Delivers no standalone article and no semantic-coverage or blind-reader independence evidence. |
| R11 | `sensitive-outbound` | Safe refusal, but no U0 sensitivity classification, outbound permission record, redaction artifact, or blocked state. |
| R12 | `no-fallback` | States the boundary, but no failure-closed runtime, authoritative status, validator evidence, or technical fallback prohibition exists. |

## RED command

```powershell
python -B -m pytest -q tests/test_ultra_repository_invariants.py tests/test_ultra_behavioral_contract.py
```

The intended RED state has no syntax, import, JSON-fixture, raw-hash, or preservation error. Passing baseline checks prove the capture is internally valid; failing target checks must identify only the absent Ultra canonical skill, generated trigger, protocol corpus, and schema corpus.

## Observed RED result

Observed with the command above:

```text
6 failed, 4 passed
```

There were no collection, syntax, import, fixture, JSON, raw-hash, preservation, or workflow-extraction errors. The four passing tests validate the frozen manifest, scenario index, raw outputs, capture conditions, annotations, and README coverage. The six intentional failures stop only at:

- missing `skills/crossframe-ultra/SKILL.md`;
- missing `crossframe-ultra` from the canonical skill inventory;
- missing `.claude/commands/crossframe-ultra.md`;
- missing Ultra protocol corpus;
- missing Ultra schema corpus.

The two repository assertions intentionally overlap with the canonical-skill and generated-trigger behavioral checks so both repository separation and product behavior remain independently frozen.
