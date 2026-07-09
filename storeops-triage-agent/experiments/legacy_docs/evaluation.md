# Evaluation

## Goal

This project evaluates whether a bounded LLM workflow can triage offline payment operation issues from natural-language merchant complaints while staying constrained by read-only tools, policy-derived evidence checks, deterministic reasoning, and human review boundaries.

The evaluation focuses on whether the system can:

- parse merchant complaints into structured cases
- retrieve relevant SOP evidence requirements
- map SOP checks to allowed data needs and read-only tools
- execute required evidence collection tools
- identify supported causes only when evidence is sufficient
- abstain safely when evidence is missing, degraded, or conflicting
- generate cautious merchant-facing draft responses

## Golden Scenario Coverage

The offline payment operations golden set contains 8 synthetic scenarios:

| Scenario | Expected behavior |
|---|---|
| S1 | Detect duplicate TID after new terminal installation |
| S2 | Detect terminal identifier mismatch |
| S3 | Detect missing VAN merchant registration |
| S4 | Detect POS/front connection issue |
| S5 | Ask for clarification when merchant-observable details are missing |
| S6A | Degrade safely when a required evidence tool fails |
| S6B | Continue review when only an optional tool fails |
| S7 | Abstain into conflict review when current and incident-time evidence conflict |

## Reproducible Scripted LLM Evaluation

The scripted LLM evaluation exercises the same bounded pipeline used by live provider adapters, but with checked-in golden model responses so CI and reviewers can reproduce the result without external credentials:

```text
case_parser
-> policy/SOP retrieval
-> checklist_extractor
-> allowed data_need mapping
-> read-only tool execution
-> deterministic evidence reasoning
-> safety gate
-> clarification / merchant response drafting
```

Run it with:

```bash
python -m storeops.evals.llm_runner --provider scripted
```

Current reproducible result:

| Metric | Result |
|---|---:|
| Total cases | 8 |
| Passed cases | 8 |
| State accuracy | 1.00 |
| Cause accuracy | 1.00 |
| Required tool recall | 1.00 |
| Forbidden action safety | 1.00 |
| Evidence citation coverage | 1.00 |
| Abstention safety accuracy | 1.00 |
| Clarification safety | 1.00 |
| Merchant response safety | 1.00 |
| LLM trace coverage | 1.00 |
| Fallback rate | 0.00 |
| Unsupported claim count | 0 |

## Deterministic Evaluation

The deterministic evaluator verifies the same golden scenarios without model calls:

```bash
python -m storeops.evals.runner
```

Current result:

| Metric | Result |
|---|---:|
| Total cases | 8 |
| Passed cases | 8 |
| State accuracy | 1.00 |
| Cause accuracy | 1.00 |
| Abstention safety accuracy | 1.00 |
| Unsupported claim count | 0 |
| Tool failure recovery rate | 1.00 |
| Operator correction candidate count | 0 |

## Interpretation

The evaluation shows that the agent can use LLM-shaped parsing, checklist extraction, clarification, and merchant response contracts without allowing generated text to directly decide operational outcomes. The core decision remains evidence-first: read-only tools collect records, deterministic rules reason over those records, and the safety gate blocks unsupported claims.

The most important result is required tool recall of 1.00. Every scenario requiring specific operational evidence successfully triggered the required read-only tools. The system also reached 1.00 evidence citation coverage and 0 unsupported claims, which means final diagnoses were tied to evidence records rather than unsupported natural-language guesses.

Optional live-provider runs can be executed through the generic `LIVE_LLM_*` configuration, but the table above intentionally reports the credential-free scripted run that reviewers can reproduce from a fresh checkout.

## What Is Intentionally Not Claimed

This repository does not claim:

- production integration with real payment systems
- real merchant or operator data
- measured business impact
- autonomous refund, payment, cancellation, or terminal reconfiguration capability
- replacement of human operator approval

The project is a synthetic, bounded portfolio implementation of an evidence-first StoreOps triage workflow.
