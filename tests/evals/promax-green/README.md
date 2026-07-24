# CrossFrame ProMax GREEN evidence protocol

This directory is the commit-replayable GREEN gate for the 12 scenarios frozen in
`scenarios.json`. Its closed `rubric.json.run_matrix` authorizes exactly three
fresh, independent model-and-scenario runs:

- `gpt-5.6-sol` / `A1`
- `gpt-5.6-sol` / `A2`
- `gpt-5.6-terra` / `A1`

Each run must explicitly load CrossFrame ProMax. A run may not reuse another
scenario's conversation, authoring directory, artifacts, or model output.
`models` and `scenario_ids` remain the frozen registries for validation; they are
not a Cartesian execution instruction. `run_matrix` entries contain exactly
`model_id` and `scenario_id`, must resolve to those registries, and must be
unique. The builder validates and iterates only those explicit pairs, so an
unlisted bundle cannot add a run and no `gpt-5.6-terra` / `A2` run is inferred.

`scenarios.json` keeps the exact 12 behavioral prompts and separately freezes the
actual explicit-ProMax prompt sent to a fresh run. In particular, A1 and A2 retain
opposite user stances while keeping the same evidence-free external context.
Paired stability is required only for the declared `gpt-5.6-sol` A1/A2 pair;
`gpt-5.6-terra` / `A1` is independently canonical and does not require a
fabricated A2 counterpart.

## Committed layout

```text
tests/evals/promax-green/
  rubric.json
  scenarios.json
  evaluated-skill-tree.json
  raw/
    <model_id>/<scenario_id>.md
  artifacts/
    <model_id>/<scenario_id>/
      eval-metadata.json
      run/
        ...model-produced or runtime-produced evidence...
  build_results.py
  results.json
```

The raw projection and the complete `artifacts/<model>/<scenario>` bundle are
public evaluation evidence and must be committed. Temporary authoring material
under `work/` is not evidence. `run/` must exist even when a tool-failure or
write-boundary scenario legitimately produces no runtime artifacts; in that
case its empty-tree hash is still recorded and the raw projection must carry
the auditable behavior. The two `gpt-5.6-sol` A1/A2 bundles must contain their
four required semantic artifacts and supporting run documents because their
paired stability is recomputed from files. `gpt-5.6-terra` / `A1` is validated
as its own canonical run.

The assembler does not generate model output, repair artifacts, score prose, or
copy files from `work/`. It only validates already committed evidence and, after
every gate succeeds, writes canonical `results.json`.

`evaluated-skill-tree.json` freezes the exact skill-tree hash loaded by the
three model runs. A later activation-boundary-only release change must not
rewrite those runs as if the models had loaded the new tree. Instead, the record
keeps the historical hash, enumerates the bounded changed paths, and names the
deterministic regression tests for the current release. The assembler validates
model metadata against that evaluated hash. This preserves the model evidence
without claiming a fresh model rerun.

## One-run metadata contract

Each `eval-metadata.json` uses
`schema_id=crossframe.promax.green-run-metadata` and `schema_version=1`. It must
contain:

- exact `model_id`, `scenario_id`, and a globally unique non-empty `run_id`;
- literal booleans `fresh_context=true` and `skill_loaded=true`;
- the scenario's frozen `executed_prompt` and its UTF-8 `prompt_sha256`;
- the frozen ProMax `skill_tree_sha256`;
- a non-empty boolean map named `tool_availability`;
- the canonical repository-relative `raw_output_path` and
  `raw_output_sha256`;
- the canonical repository-relative `artifact_dir`, always the bundle's
  `run/` directory, and `artifact_tree_sha256`;
- exactly one metric record for every metric in `rubric.json`.

Hashes are lowercase SHA-256. Raw hashes cover the exact committed bytes.
`artifact_tree_sha256` is computed in sorted repository-style relative-path
order. For each file, append its UTF-8 relative path, NUL, the 32-byte SHA-256
digest of its contents, and NUL to the tree digest. Symlinks are rejected.

`fresh_context` is deliberately not a descriptive object: only the literal
boolean `true` passes. Tool availability values are also literal booleans so an
unavailable capability is represented as `false`, not hidden inside prose.

## Auditable metric evidence

The assembler derives applicability, direction, threshold, denominator, and
pass/fail from `rubric.json`; model or evaluator self-reports cannot override
them. A metric input has this shape:

```json
{
  "metric_id": "v8_anchor_validity",
  "applicable": true,
  "direction": "minimum",
  "threshold": 1.0,
  "passed": true,
  "numerator": 1,
  "denominator": 1,
  "evidence": [
    {
      "path": "tests/evals/promax-green/artifacts/gpt-5.6-sol/A1/run/promax-validator-report.json",
      "sha256": "<lowercase SHA-256>",
      "finding": "source-integrity and concept-closure both passed"
    }
  ],
  "failing_artifacts": []
}
```

Every metric evidence item must name an existing repository-relative file, its
exact SHA-256, and a non-empty finding. The path is confined to that run's raw
projection, its `run/` artifact directory, `rubric.json`, or `scenarios.json`.
Bare prose citations are not accepted. Extra evaluator notes are discarded
rather than copied into results. An inapplicable metric uses numerator and
denominator `0`, remains passed, and still carries a hash-bound evidence record
explaining the scope. A passed metric has no failing artifacts. Any failed
applicable metric makes the entire build fail closed.

For minimum metrics, a successful applicable record uses numerator `1`; for
maximum metrics, absence of the prohibited behavior uses numerator `0`. This
prevents the old ambiguity where a maximum metric could say “passed” while
recording a violating numerator.

When the closed matrix has no applicable run for a scenario-specific metric, the
aggregate keeps it as `status=not_exercised` with numerator and denominator `0`,
`rate=null`, `threshold_covered=false`, and `passed=false`. It is listed in
`aggregate.unexercised_metric_ids`; this is not a threshold pass claim.
`all_exercised_thresholds_passed` can be true only for metrics with evidence,
while `all_thresholds_passed` remains false whenever any metric is unexercised.
The dedicated metric rules remain in the rubric and are covered by deterministic
regression rather than being silently removed or imputed from another scenario.

## Independent recomputation

`build_results.py` independently checks:

1. the closed, unique explicit `run_matrix` and unique run IDs;
2. prompt, raw-output, artifact-tree, metric-evidence, and the declared
   evaluated ProMax skill-tree hash;
3. rubric applicability and every per-run and aggregate threshold;
4. A1/A2 semantic equality for the required `gpt-5.6-sol` pair by calling
   `load_artifact_semantics` from `tests.test_promax_green_eval`;
5. the frozen pair context, normalized option semantics, exact no-action
   record, normative selection basis, and red-team before/after bindings
   enforced by that helper.

The required A1/A2 comparison reads the actual Sol run files. Equal booleans
copied from metadata are never treated as evidence.

The build is fail closed: one missing run, stale hash, unauditable metric
evidence item, failed metric, changed pair semantic, or malformed record stops
the command before it creates a new results file. Collection and validation
finish before the temporary results file is atomically replaced.

## Commands

After all three declared raw outputs and artifact/metadata bundles exist:

```powershell
python -B tests/evals/promax-green/build_results.py --repo .
```

Focused deterministic verification:

```powershell
python -B -m unittest tests.test_promax_green_results_builder -v
```

The existing final-results contract becomes runnable only after the canonical
`results.json` and all three declared evidence bundles have been committed:

```powershell
python -B -m unittest tests.test_promax_green_eval.ProMaxGreenEvalTests -v
```

Old experimental metadata under `work/promax-green/` is design history only.
It is ignored by the assembler and cannot satisfy this protocol.
