# CrossFrame Ultra versus ProMax benchmark

This directory freezes the deterministic contract for 24 matched cases. It does not generate model output, grades, scores, winners, release claims, or forward-validation claims.

The committed `results.json` must remain `not_run` until all 48 product runs and all 72 raw grade files from three fresh blind graders per case exist and pass hash validation. The builder must fail closed: missing evidence, missing hashes, unexpected aggregate fields, fallback runtimes, or changed raw bytes are errors. It never treats prose summaries or hand-authored totals as authority.

## Legal state machine

The only legal transition is `scaffold -> execution-ready -> ready-for-results-build`:

The checked-in schema-v1 scaffold may be inspected with `validate_scaffold`. The execution transition accepts it only as a fully validated source: after all 24 schema-v2 bundles and their final packet/tree bindings pass in memory, one atomic replacement writes a schema-v2 `execution-ready` manifest. A schema-v1 manifest is never marked executable, and an already-schema-v2 scaffold follows the same validation gate.

1. `scaffold`: every pair and product is pending, skill-tree hashes are null, case material reviews are pending, and `results.json` is exactly `not_run`.
2. `execution-ready`: the transition command requires 24 frozen evidence bundles; three distinct leakage, privacy, and license reviewers bound to the complete source set; an exact per-source license decision; closed default-deny packet allowlists; both product skill-tree SHA-256 values; and a `raw/` root containing only `.gitkeep`. The two CLI hashes are expected assertions, not caller-selected values: the builder remeasures the fixed `skills/crossframe-promax` tree and requires a fresh, ready Ultra U1 measurement from fixed `skills/crossframe-ultra`. It binds shared product-packet and grader-base-packet hashes, then replaces the pairing manifest once. No product result exists yet.
3. `ready-for-results-build`: the second transition verifies both completed product runs and all three hash-bound blind grades for every case. Every product and grade records a canonical `run_id`/`receipt_sha256` fresh-context receipt; all 48 product IDs and all 72 grade IDs must be unique. Only then does it seal 24 completed pairs. `results.json` is still exactly `not_run`.
4. Only the frozen rebuild command below may derive and atomically write a complete result. Direct jumps, partial pairs, hand-authored aggregate fields, missing hashes, and rewrites of the `not_run` placeholder during either transition fail closed.

The committed `scaffold`/`not_run` assertions are pre-execution assertions only, not Task 17 final acceptance. Once the real benchmark is complete, Task 17 must replace those committed-state expectations with final-evidence assertions: manifest status `ready-for-results-build`, 24 completed pairs, 48 hash-bound product runs, 72 hash-bound blind grades, a derived `complete` result, and verified raw references. Leaving a pending assertion as the final benchmark contract is a failure.

After evidence review, prepare execution with:

```powershell
python -B tests/evals/ultra-vs-promax/build_results.py --repo-root . --eval-root tests/evals/ultra-vs-promax --output tests/evals/ultra-vs-promax/results.json --transition-to execution-ready --promax-skill-tree-sha256 <64-lowercase-hex> --ultra-skill-tree-sha256 <64-lowercase-hex>
```

After all raw outputs and grades are present, seal completed pairs with:

```powershell
python -B tests/evals/ultra-vs-promax/build_results.py --repo-root . --eval-root tests/evals/ultra-vs-promax --output tests/evals/ultra-vs-promax/results.json --transition-to ready-for-results-build
```

## Frozen rebuild CLI

Task 17 and independent reviewers rebuild `results.json` with this exact command from the repository root:

```powershell
python -B tests/evals/ultra-vs-promax/build_results.py --repo-root . --eval-root tests/evals/ultra-vs-promax --output tests/evals/ultra-vs-promax/results.json
```

The command revalidates the 24 pair bindings, all fresh-context receipts and global ID uniqueness, both product run metadata records per case, raw output SHA-256 values, artifact-tree SHA-256 values, and all three blind-grade files before atomically replacing `results.json`. On any error it exits non-zero and leaves the existing placeholder or prior derived result byte-for-byte unchanged.

## Evidence boundary

`scenarios.json`, `rubric.json`, `pairing-manifest.json`, the case skeletons, this README, the empty raw registry, and the builder are deterministic scaffolding. They are not benchmark performance evidence. Expected-pressure files are audit-only and hidden from products and graders. Frozen case materials must pass outcome-leakage, privacy, and license review before product execution.

Product packets contain only the prompt, evidence cutoff, and declared material sources. Grader packets contain only those product-packet files, the scoring rubric, and logical `Article A` / `Article B` slots; they contain no case ID, grader ID, product identity, or directory hint. Material manifests, privacy policies, expected-pressure files, product identities, raw paths, and prior grades are audit-only and never enter either packet.

Actual model runs belong under `raw/<case-id>/<product>/`; blind grades belong under `raw/<case-id>/grades/`. No fallback product is allowed. Product names, pairing metadata, runtime internals, directory names, expected-pressure metadata, and prior grades remain hidden from graders.

Forward prediction evidence is governed separately by `../ultra-forward/`. This deterministic scaffold makes no forward-validation claim.
