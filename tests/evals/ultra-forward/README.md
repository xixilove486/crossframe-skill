# CrossFrame Ultra forward-validation registry

`forecast-registry.jsonl` holds append-only paired original forecast records. `resolutions.jsonl` holds later append-only resolution records that bind the immutable original record hash; resolution data never rewrites an original forecast.

Both committed registries are empty. This scaffold does not claim forward-validated status, predictive superiority, resolved cases, or any observed outcome.

A later release may claim forward validation only with at least 30 independent resolved cases across at least five domains and three time horizons. ProMax and Ultra must use matched model, request, evidence, and tool bindings while preserving each product's immutable forecast declaration. Evaluation uses paired, case-clustered resampling and requires stable positive Ultra advantage in direction, time-window coverage, declared-indicator resolution, and admissible probability scoring.

Every appended resolution binds its original pair, forecast artifact, forecast record, and resolution-event SHA-256 values. The evaluator recomputes outcome consistency and Brier scores, rejects duplicate independence clusters, and fails closed on mutation or incomplete records.
