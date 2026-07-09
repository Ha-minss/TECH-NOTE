# Architecture

## Design intent

The repository is organized around a reusable workflow engine plus a single domain pack and an operator-facing product layer.

- `src/storeops/core/` contains domain-agnostic orchestration contracts and execution flow.
- `src/storeops/domains/offline_payment_ops/` contains offline payment parsing, evidence rules, reasoner rules, safety rules, fixture loading, and workflow wiring.
- `src/storeops/operator/` contains the review experience, approval state, handoff payloads, and feedback capture.

## Workflow pipeline

```text
merchant complaint
-> parser
-> policy retrieval
-> planner
-> read-only tools
-> evidence builder
-> reasoner
-> safety gate
-> operator brief
```

The `core` layer knows how the pipeline runs. The `offline_payment_ops` domain pack knows how this specific incident family should be interpreted. The `operator` layer turns the workflow result into something a human can review, approve, and hand off safely.

## Public entrypoints

The public command-line entrypoint is `storeops.apps.operator_cli`. Web export and release packaging live under `storeops.apps.operator_web` and `storeops.apps.release_artifacts`.

## Safety boundary

The tool layer is intentionally read-only. The system can inspect synthetic records and produce a grounded brief, but it does not mutate payment configuration, change a TID, trigger a refund, or execute merchant-facing operational actions automatically.

## Quality systems

Evaluation, observability, and the feedback loop are first-class parts of the design.

- `src/storeops/evals/` runs deterministic regression checks
- `src/storeops/observability/` records trace and cost metadata
- `src/storeops/feedback_loop/` captures review corrections for later promotion into evaluation datasets
