# AMEX Credit Risk Decisioning Portfolio

AMEX default prediction scores are converted into a manual review decisioning workflow.

The project does not present the score as a fully calibrated probability of default. Instead, it treats the score as a ranking-oriented signal for review prioritization, policy simulation, and monitoring.

## Project Question

Given limited review capacity, which customers should the risk team review first?

## Public Repository Design

The original Colab experiment used large AMEX customer-month parquet files, feature engineering, several model families, and blended OOF scores. Those raw files and full training artifacts are not included in this public repository.

This public version focuses on the decisioning layer using:

- masked public score samples,
- aggregate risk bucket outputs,
- Top-K policy simulation tables,
- weighted non-default correction tables,
- normalized cost scenario outputs.

## Key Results

- D1 default rate: **96.59%**
- D10 default rate: **0.04%**
- Best Base scenario threshold: **Top 17%**
- Base normalized net benefit: **4,365.15**

## Notebook Flow

1. `01_project_overview_and_score_release.ipynb`
   - public artifact inventory
   - masked score sample check
   - original pipeline summary

2. `02_risk_ranking_validation.ipynb`
   - risk decile validation
   - risk band monitoring
   - cumulative default capture

3. `03_policy_simulation_and_cost_scenarios.ipynb`
   - Top-K review trade-off
   - weighted non-default correction
   - normalized net benefit scenario comparison
   - final policy interpretation

## Main Figures

### Risk Bucket / Decile Validation

![Risk bucket decile validation](outputs/figures/risk_bucket_decile_validation.png)

The highest-risk decile, D1, shows a 96.59% observed default rate, while the lowest-risk decile, D10, shows a 0.04% observed default rate.

### Normalized Net Benefit by Review Scope

![Normalized net benefit](outputs/figures/normalized_net_benefit_by_review_scope.png)

Under the Base scenario, Top 17% produces the strongest normalized net benefit.

## Repository Structure

```text
amex-credit-risk-portfolio-public/
|-- README.md
|-- requirements.txt
|-- notebooks/
|   |-- 01_project_overview_and_score_release.ipynb
|   |-- 02_risk_ranking_validation.ipynb
|   `-- 03_policy_simulation_and_cost_scenarios.ipynb
|-- outputs/
|   |-- figures/
|   `-- tables/
|-- data/
|   |-- README.md
|   `-- sample/
|-- src/
|   |-- preprocessing/
|   |-- modeling/
|   `-- evaluation/
`-- docs/
    |-- technical_note.md
    `-- governance_and_limitations.md
```

## Run

```powershell
python -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path .tmp\.jupyter-runtime | Out-Null
$env:TEMP=(Resolve-Path .tmp).Path
$env:TMP=(Resolve-Path .tmp).Path
$env:TMPDIR=(Resolve-Path .tmp).Path
$env:JUPYTER_RUNTIME_DIR=(Resolve-Path .tmp\.jupyter-runtime).Path
$env:JUPYTER_ALLOW_INSECURE_WRITES='1'

$notebooks = @(
  "notebooks/01_project_overview_and_score_release.ipynb",
  "notebooks/02_risk_ranking_validation.ipynb",
  "notebooks/03_policy_simulation_and_cost_scenarios.ipynb"
)

foreach ($nb in $notebooks) {
  python -m nbconvert --log-level ERROR --to notebook --execute $nb --inplace
}
```

## Governance Note

This is a portfolio prototype for manual review prioritization and monitoring support. It is not an automatic adverse-action system. Production use would require calibration validation, drift monitoring, compliance review, fairness checks, access control, and audit logging.
