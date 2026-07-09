# StoreOps Triage Agent

StoreOps Triage Agent is a bounded LLM workflow for offline payment operations. It turns a merchant complaint into a structured case, plans read-only evidence collection, runs deterministic tools against a synthetic SQLite fixture, and produces an operator-review decision without mutating payment or configuration state.

The submission runtime is intentionally small: the canonical dataset is the 50-case synthetic offline-payment set, and older S1-S7 demo assets live under `experiments/`.

## Canonical Assets

```text
data/fixtures/offline_payment_ops_synthetic_50.sqlite3
data/fixtures/offline_payment_ops_synthetic_50_manifest.json
data/golden/offline_payment_ops_cases_50.json
data/evaluation/retrieval_cases_50.json
data/evaluation/planner_cases_50.json
data/policies/offline_payment_ops/
data/tool_catalog/offline_payment_ops_tools.json
reports/synthetic_50_validation_report.md
reports/synthetic_50_validation_matrix.csv
scripts/generate_offline_payment_synthetic_50.py
```

## Run

PowerShell from the project root:

```powershell
$env:PYTHONPATH = "src"
python -m storeops.evals.runner
```

Expected deterministic summary for the canonical 50-case dataset:

```json
{
  "total_cases": 50,
  "passed_cases": 38,
  "state_accuracy": 0.9,
  "cause_accuracy": 0.98,
  "abstention_safety_accuracy": 1.0,
  "unsupported_claim_count": 0
}
```

## Live LLM Evaluation

The live provider accepts OpenAI-compatible chat-completions APIs.

```powershell
$env:PYTHONPATH = "src"
$env:LIVE_LLM_API_KEY = "your_key"
$env:LIVE_LLM_BASE_URL = "https://api.deepseek.com"
$env:LIVE_LLM_MODEL = "deepseek-chat"
$env:LIVE_LLM_TIMEOUT_SECONDS = "20"

python -m storeops.evals.llm_runner `
  --provider live `
  --fixture-key SYN-001 `
  --output-dir experiments/eval_runs/llm/deepseek_smoke_SYN001
```

Remove `--fixture-key SYN-001` to run all 50 cases.

## Test

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q -p no:cacheprovider
```

## Repository Layout

```text
src/storeops/core/                         workflow contracts, planner, evidence, safety
src/storeops/domains/offline_payment_ops/  domain parser, evidence rules, reasoner, gateway, workflow
src/storeops/evals/                        deterministic and LLM evaluation runners
src/storeops/infra/                        SQLite open/create helpers and read-only tool gateway base
src/storeops/llm/                          bounded LLM components and live provider adapter
src/storeops/observability/                metrics and trace serialization
data/                                      canonical synthetic 50 fixtures and policy inputs
reports/                                   synthetic dataset validation evidence
scripts/                                   dataset generation script
experiments/                               legacy demos, old tests, prior outputs, exploratory assets
```

## Safety Boundary

The agent can parse, plan, retrieve evidence, and draft cautious operator-facing output. It cannot execute payments, issue refunds, mutate TID/VAN/POS/merchant configuration, or claim a fix without evidence. Missing, failed, or conflicting evidence routes to clarification, degraded review, or conflict review.
