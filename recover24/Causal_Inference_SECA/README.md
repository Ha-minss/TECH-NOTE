# Korea SECA → Kyushu SO₂ (Step 1, 2020-09)

Maritime shipping is a major source of SO₂ emissions, and sulfur fuel regulations can reduce sulfur pollution locally and potentially downwind. Korea implemented **SECA Step 1 in Sep 2020**, and this project examines whether SO₂ concentrations in **Kyushu, Japan** shifted downward after the policy. Using a coastal–inland comparison, we ask whether the **coastal–inland SO₂ gap** in Kyushu becomes more negative after 2020-09. The results show a **~10% downward shift (directionally consistent across main specifications)**.

This repository provides a **reproducible evaluation** using (i) a **coastal–inland DID** with **station and month fixed effects** and **station-clustered** standard errors, and (ii) an **event study** centered at **2020-09** to assess dynamics and pre-trends.
- **Study window:** 2017-01 to 2021-12  
- **Unit:** station × month (Kyushu)  
- **Inference:** 1-way cluster by station (main results)  
- **Scope:** Korea SECA Step 1 only (run-and-reproduce bundle)

---

## What you get (outputs)

This repo regenerates:

- **Main DID table (3 specs):** `outputs/tables/main_did_step1.csv`
- **Event-study coefficients:** `outputs/tables/event_study_step1.csv`
- **Event-study plot:** `outputs/figures/event_study_step1.png`
- **Robustness suite:** `outputs/tables/robustness_suite_step1.csv`
- **Treatment-definition robustness:** `outputs/tables/treatment_defs_step1.csv`
- **Level SO₂ checks (OLS/PPML):** `outputs/tables/level_so2_ols_ppml_step1.csv`

> Quick visual check: open `outputs/figures/event_study_step1.png`.

---

## Design

**Research question.** After Korea’s SECA Step 1 (2020-09), does the **coastal–inland SO₂ gap in Kyushu** shift **downward**?

**Empirical strategy.**
- TWFE DID: station FE + month FE, station-clustered SE
- Event study centered at **2020-09**, window **[-12, +12]**, reference **k = -1**
- Robustness: weather variants, econ lags, time placebos, alternative coastal definitions
- Level-outcome checks: OLS + PPML on level SO₂ (ppb)

---

## Repository layout

```text
data/
  df_iv.csv                      # trimmed station×month panel (included)
scripts/
  01_main_did_step1.py
  02_event_study_step1.py
  03_robustness_suite_step1.py
  04_level_so2_ols_ppml.py
  05_treatment_defs_step1.py
  00_prepare_df_iv_for_github.py # optional: re-make trimmed dataset
outputs/
  tables/
  figures/
step1_did/                       # reusable helpers + config
requirements.txt
````

---

## Quickstart

### 1) Install

```bash
pip install -r requirements.txt
```

### 2) Run (local)

```bash
python scripts/01_main_did_step1.py
python scripts/02_event_study_step1.py
python scripts/03_robustness_suite_step1.py
python scripts/05_treatment_defs_step1.py
python scripts/04_level_so2_ols_ppml.py
```

All outputs are saved under `outputs/`.

---

## Run in Google Colab (optional)

In Colab, local packages may not be discoverable by default.
If you see `ModuleNotFoundError: No module named 'step1_did'`, run with `PYTHONPATH=$PWD`:

```bash
%cd /content/Portfolio/Causal_Inference_SECA
!pip install -r requirements.txt

!PYTHONPATH=$PWD:$PYTHONPATH python scripts/01_main_did_step1.py
!PYTHONPATH=$PWD:$PYTHONPATH python scripts/02_event_study_step1.py
!PYTHONPATH=$PWD:$PYTHONPATH python scripts/03_robustness_suite_step1.py
!PYTHONPATH=$PWD:$PYTHONPATH python scripts/05_treatment_defs_step1.py
!PYTHONPATH=$PWD:$PYTHONPATH python scripts/04_level_so2_ols_ppml.py
```

---

## Data notes

* `data/df_iv.csv` is a **trimmed** panel that includes only columns needed to reproduce the results in this repo.
* To run with your own panel, replace `data/df_iv.csv` (same column names required).

### Optional: rebuild a shareable trimmed dataset

```bash
python scripts/00_prepare_df_iv_for_github.py
```

---

## Citation

If you use this repository or its outputs, please cite:

Park, Dongha. *Korea SECA → Kyushu SO₂: Step 1 Policy Evaluation (Reproducible DID + Event Study).* (Year).
Repository: [https://github.com/Ha-minss/Portfolio/tree/main/Causal_Inference_SECA](https://github.com/Ha-minss/Portfolio/tree/main/Causal_Inference_SECA)

### BibTeX (optional)

```bibtex
@misc{park_seca_kyushu_step1,
  author       = {Park, Dongha},
  title        = {Korea SECA → Kyushu SO2: Step 1 Policy Evaluation (Reproducible DID + Event Study)},
  year         = {2026},
  howpublished = {\url{https://github.com/Ha-minss/Portfolio/tree/main/Causal_Inference_SECA}},
  note         = {Accessed 2026-01-07}
}
```

---

## Contact

If you find a bug or want to reproduce a specific table/figure, open an issue (or message me) with:

* script name
* exact command you ran
* full error log
