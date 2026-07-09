# StoreOps Triage Agent

LLM-enabled StoreOps Triage Agent is a bounded LLM workflow for offline payment operations. It turns a merchant complaint into a structured case, plans read-only evidence collection, runs deterministic tools, and prepares an operator review package without mutating payment or configuration state.

This is not an open-ended chatbot. The LLM is allowed to help with language-heavy steps, but final decisions are constrained by read-only tools, evidence records, deterministic reasoners, safety gates, and human operator review.

## What This Demonstrates

- A merchant can describe an offline payment issue in natural language.
- The LLM parses the case and plans which internal data should be checked.
- The workflow executes only read-only tools against synthetic StoreOps fixtures.
- Evidence normalization, deterministic reasoning, and safety gates control the final state.
- Unclear, failed-tool, and conflicting-evidence cases abstain instead of forcing a diagnosis.
- The LLM can generate safe clarification questions and cautious merchant-facing draft copy.
- S1-S7 scenarios are covered by deterministic and LLM-scripted evaluation suites.

## LLM Boundaries

## RAG As Evidence Checklist Source

RAG is used as the source of operational evidence checks, not as answer decoration. The workflow retrieves SOPs, extracts the checks those SOPs say should be verified, maps each check to an allowed `data_need` in the tool catalog, and then executes the existing read-only tools. S1-S7 are regression scenarios for this structure, not case-specific hardcoded rules.

Each checklist-derived tool call records a trace with `policy_id`, `policy_title`, `check_text`, `matched_data_need`, `tool_name`, `priority`, `reason`, `source_quote`, and `source`. This makes it auditable why a tool such as `get_tid_config` ran: it came from a retrieved SOP check mapped to `payment_identifier_config`, not from a case-id shortcut.
The LLM is used in four bounded components:

- Case Parser: structures the merchant complaint into issue family, symptoms, context flags, and missing fields.
- Evidence Planner: selects allowed data needs that map to known read-only tools.
- Clarification Question Generator: asks only merchant-observable questions when information is missing.
- Merchant Response Drafter: drafts cautious customer-facing copy from confirmed facts and workflow state.

The LLM is not allowed to:

- execute payments
- issue refunds
- mutate TID, VAN, POS, or merchant configuration
- make unsupported final root-cause claims
- claim an issue is fixed or completed without evidence
- bypass operator review or approval boundaries

## Scenario Coverage

The end-to-end golden set lives in `data/golden/offline_payment_ops_cases.json` and covers:

- S1 `duplicate_tid`: new terminal installation causes duplicate TID evidence.
- S2 `terminal_identifier_mismatch`: physical terminal identity differs from registered records.
- S3 `van_merchant_registration_missing`: VAN merchant registration is incomplete.
- S4 `pos_front_connection_issue`: POS/front request delivery or connection logs show failure.
- S5 `needs_clarification`: merchant message lacks observable details.
- S6A `required_tool_failure`: required TID lookup fails and the case degrades safely.
- S6B `optional_tool_failure`: optional routing failure does not block evidence-backed review.
- S7 `conflict_review`: current and incident-time evidence conflict, so the workflow abstains.

Additional focused datasets live in:

- `data/evaluation/retrieval_cases.json`
- `data/evaluation/planner_cases.json`

## Evaluation

Deterministic evaluation validates the rule/evidence workflow:

```bash
python -m storeops.evals.runner
```

LLM scripted evaluation validates the bounded LLM parser, planner, clarification, and response drafting flow without calling a live API:

```bash
python -m storeops.evals.llm_runner --provider scripted
```

Final evaluation results are summarized in `docs/evaluation.md`.

Core LLM metrics include state accuracy, cause accuracy, required tool recall, forbidden action safety, evidence citation coverage, abstention safety, clarification safety, merchant response safety, LLM trace coverage, fallback rate, and unsupported claim count.

## Run Locally

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
python -m storeops.evals.runner
python -m storeops.evals.llm_runner --provider scripted
python -m storeops.apps.demo S1 --provider scripted-demo
```

On Windows without editable install, set `PYTHONPATH` first:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m storeops.evals.runner
python -m storeops.evals.llm_runner --provider scripted
python -m storeops.apps.demo S1 --provider scripted-demo
```


## Product Console

The portfolio console presents the workflow as a SaaS-style operator review product rather than a raw CLI demo. It separates the daily review queue, per-case approval screen, issue analytics, evidence trace, and evaluation report.

```bash
python -m pip install -e .[console]
streamlit run src/storeops/apps/portfolio_console.py
```

The console is a thin UI layer over the same scripted workflow used by tests and evaluations. It shows operator approval posture, missing information, conflicting evidence, read-only tool calls, evidence records, and safe merchant response drafts.
## Optional Live LLM Demo

Live LLM calls are optional and are never used by CI. Keep local credentials uncommitted.

```bash
cp config/live.local.example.json config/live.local.json
# fill api_key, model_name, and base_url locally
python -m storeops.apps.demo S1 --provider live --config config/live.local.json
```

Release artifact pages are generated under `docs/demo/` when you run `python -m storeops.apps.release_artifacts`. See `docs/llm-integration.md` for the provider contract and local setup notes.

## Repository Layout

```text
storeops-triage-agent/
  config/
  data/
    golden/
    llm/scripted_responses/
  docs/
  src/storeops/
    apps/
    core/
    domains/offline_payment_ops/
    evals/
    infra/
    llm/
    observability/
    operator/
  tests/
```

## Safety Posture

The project intentionally favors bounded review over autonomous action. When evidence is missing, tools fail, or records conflict, the workflow moves to `NEEDS_CLARIFICATION`, `DEGRADED_REVIEW`, or `CONFLICT_REVIEW` rather than inventing a cause.


