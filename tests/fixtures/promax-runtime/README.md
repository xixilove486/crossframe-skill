# ProMax runtime fixtures

`scenarios.json` is the canonical catalog for generated runtime fixtures. The fixture factory materializes each scenario from the same valid v8-bound baseline, then applies exactly one named mutation.

The repository stores mutation specifications instead of generated runs because a complete run contains 3,980 source-read events and 709 concept dispositions. Tests generate those artifacts in an isolated temporary directory and validate the declared outcome.

The positive fixture must pass strict completion. The incomplete fixture must retain useful artifacts while reporting structured incompleteness. Every adversarial fixture must fail for its declared error type.
