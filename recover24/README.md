# NLP PROJECT

This repository contains NLP/LLM projects focused on information extraction, document automation, evaluation workflows, and safety-oriented AI systems.

## Project 01. Recover24 V3

**Recover24 V3** is an NLP/LLM-based recovery workflow for financial fraud incidents.
The project focuses on converting victim statements and structured form inputs into safer, reviewable recovery documents.

The main goal is not to let an LLM make final safety decisions. Instead, the system uses LLMs only where natural language understanding is useful, while deterministic code handles conflict detection and document generation safety gates.

---

## Core Idea

Recover24 V3 evaluates whether a financial fraud recovery document can be safely generated from user-provided information.

The workflow separates the problem into three evaluation tracks:

| Track                        | Purpose                                                                                | LLM Used? |
| ---------------------------- | -------------------------------------------------------------------------------------- | --------- |
| A. Normalization & Rendering | Normalize form inputs into canonical JSON and verify rendered document fields          | No        |
| B. Narrative Fact Coverage   | Judge whether generated narratives include required facts and avoid unsupported claims | Yes       |
| C. Consistency & Safety Gate | Extract facts from free-form statements and detect conflicts with form inputs          | Yes       |

---

## System Design

### A. Form Normalization & Rendering

This track checks whether structured form inputs are correctly normalized into canonical fields.

Example:

```text
Input: 17915000원
Canonical: damage_amount_krw = 17915000
Rendered: 17,915,000원
```

This step is deterministic and does not use an LLM.

---

### B. Narrative Fact Coverage

This track evaluates whether a generated incident narrative includes required elements such as:

* Damage amount
* Police report status
* Required recovery-related facts
* Unsupported or contradictory claims

DeepSeek is used as an LLM judge for semantic evaluation.

The judge returns structured labels such as:

```json
{
  "elements": [
    {
      "id": "amount",
      "label": "present",
      "evidence": "피해금액은 17,915,000원"
    }
  ],
  "unsupported_claims": [],
  "contradictions": []
}
```

---

### C. Consistency & Safety Gate

This is the safety-critical track.

The LLM extracts candidate facts from the victim's free-form statement.

Example:

```text
Raw statement:
총 30415000원을 송금했습니다.
```

The LLM extractor returns:

```json
{
  "statement_facts": {
    "damage_amount_krw": 30415000
  }
}
```

Then deterministic code compares the extracted statement facts against the form facts.

Example:

```text
Form amount: 17,915,000원
Statement amount: 30,415,000원

Result:
- Conflict detected
- Document generation blocked
- Human review required
```

The LLM does not decide whether to block the document.
The final safety decision is handled by deterministic conflict-checking logic.

---

## Evaluation Results

Current MVP evaluation uses datasets derived from existing Recover24 gold cases.

| Evaluation Track             |                   Cases | Result |
| ---------------------------- | ----------------------: | ------ |
| A. Normalization & Rendering |                      20 | Passed |
| B. Narrative LLM Judge       | 18 eligible / 2 skipped | Passed |
| C. Consistency LLM Extractor |                      20 | Passed |

Latest local test result:

```text
74 passed
```

DeepSeek evaluator integration was verified with no fallback usage:

```text
Narrative judge:
- judge_mode = llm
- judge_fallback_count = 0
- element_recall = 1.0

Consistency extractor:
- extractor_mode = llm
- extractor_fallback_count = 0
- extractor_accuracy = 1.0
- conflict_recall = 1.0
- conflict_precision = 1.0
- blocking_accuracy = 1.0
- false_block_rate = 0.0
```

---

## Project Structure

```text
Recover24_V3/
├─ recover24/
│  └─ providers/
│     ├─ base.py
│     ├─ gemma_colab.py
│     └─ deepseek.py
│
├─ evaluation/
│  ├─ run_all.py
│  ├─ llm_json.py
│  ├─ build_abc_datasets_from_gold.py
│  │
│  ├─ normalization/
│  │  ├─ dataset.jsonl
│  │  ├─ normalizer.py
│  │  ├─ renderer_check.py
│  │  ├─ metrics.py
│  │  └─ runner.py
│  │
│  ├─ consistency/
│  │  ├─ dataset.jsonl
│  │  ├─ extractor.py
│  │  ├─ llm_extractor.py
│  │  ├─ conflict_checker.py
│  │  ├─ metrics.py
│  │  └─ runner.py
│  │
│  ├─ narrative/
│  │  ├─ dataset.jsonl
│  │  ├─ checklist.py
│  │  ├─ judge.py
│  │  ├─ metrics.py
│  │  └─ runner.py
│  │
│  └─ gold/
│     ├─ master_cases.jsonl
│     └─ dataset_build_stats.json
│
├─ tests/
├─ README.md
├─ requirements.txt
├─ .gitignore
└─ .env.example
```

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment variables if using DeepSeek:

```bash
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.1
DEEPSEEK_MAX_TOKENS=1024
```

Do not commit real API keys.

---

## Run Tests

```bash
python -m pytest -q
```

Expected result:

```text
74 passed
```

---

## Run All Evaluations

```bash
python -m evaluation.run_all
```

---

## Run Individual Evaluation Tracks

### A. Normalization

```bash
python -m evaluation.normalization.runner
```

### B. Narrative Judge

Checklist mode:

```bash
python -m evaluation.narrative.runner --judge checklist
```

DeepSeek LLM judge mode:

```bash
python -m evaluation.narrative.runner --judge llm --provider deepseek --timeout 240
```

### C. Consistency Extractor

Rule extractor mode:

```bash
python -m evaluation.consistency.runner --extractor rule
```

DeepSeek LLM extractor mode:

```bash
python -m evaluation.consistency.runner --extractor llm --provider deepseek --timeout 240
```

---

## Safety Principle

Recover24 V3 follows a hybrid LLM + deterministic safety architecture.

The LLM is used for:

* Extracting facts from natural language statements
* Judging whether generated narratives preserve required information
* Identifying missing, unsupported, or contradictory narrative elements

Deterministic code is used for:

* Canonical normalization
* Field-level comparison
* Conflict detection
* Blocking unsafe document generation
* Human review routing

This design avoids relying on the LLM for final safety-critical decisions.

---

## Current Limitations

This is an MVP evaluation workflow, not a production fraud recovery system.

Current limitations:

* The evaluation dataset is small and gold-case-derived.
* The narrative track evaluates generated text but does not yet run a full end-to-end document generator benchmark.
* Real-world deployment would require more diverse fraud scenarios, document templates, audit logging, privacy controls, and human approval workflows.

---

## Next Steps

Potential future improvements:

* Expand the dataset beyond the MVP 20-case tracks.
* Add more fraud incident types.
* Add full end-to-end document generation evaluation.
* Add stronger audit logs for each LLM extraction and judgment.
* Add a reviewer UI for blocked or conflicting cases.
* Compare multiple LLM providers on extraction and judging quality.
