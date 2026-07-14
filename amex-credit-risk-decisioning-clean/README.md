# AMEX Credit Risk Decisioning

Public portfolio reconstruction of a personal Kaggle AMEX Default Prediction project. The repository is designed for review by credit risk model development and validation teams: it keeps reproducible code, small aggregate outputs, and clear provenance while excluding raw data, full OOF files, trained models, and customer-level private artifacts.

This is not a card issuer production system. The score is a ranking-oriented risk score from the AMEX competition setup, not a calibrated probability of default or an automatic approval/decline model.

## What Is Included

- Feature engineering and evaluation code under [src/amex_risk](src/amex_risk)
- Experiment settings under [configs](configs)
- Verified aggregate results under [outputs/tables](outputs/tables)
- Result provenance in [docs/results_provenance.md](docs/results_provenance.md)
- Ablation and OOF diagnostic plan in [docs/ablation_and_oof_diagnostics.md](docs/ablation_and_oof_diagnostics.md)
- Single Colab notebook for feature ablation and OOF diagnostics: [notebooks/03_colab_feature_ablation_and_oof_diagnostics.ipynb](notebooks/03_colab_feature_ablation_and_oof_diagnostics.ipynb)
- Reproduction instructions in [docs/reproduction_guide.md](docs/reproduction_guide.md)
- Governance and limitations in [docs/governance_and_limitations.md](docs/governance_and_limitations.md)
- Synthetic smoke-test data only: [data/sample/synthetic_scores.csv](data/sample/synthetic_scores.csv)

## Source Of Truth

The source of truth for experiment results is the original Colab notebook `Untitled41.ipynb`. Values not visible in that notebook are not claimed here. Public tables are either copied from its aggregate outputs or manually transcribed from visible notebook outputs, with provenance recorded in [docs/results_provenance.md](docs/results_provenance.md).

## Core Results

| Result | Value | Interpretation |
|---|---:|---|
| Best recorded equal blend | AMEX `0.797631`, ROC AUC `0.962782` | 8 OOF score equal blend, including MLP and pivot-lite model |
| Ridge stacking | AMEX `0.797538`, ROC AUC `0.962718` | OOF stacking check over six base models |
| Top 1% observed precision | `99.98%` | Modeling sample ranking result |
| Top 5% observed precision | `99.11%` | Modeling sample ranking result |
| Top 5% 20x weighted scenario precision | `84.79%` | AMEX competition sampling-adjusted scenario |
| D1 default rate | `96.59%` | Highest-risk decile in modeling sample |
| D10 default rate | `0.04%` | Lowest-risk decile in modeling sample |

## Policy Simulation Boundary

The Top 17% result is not described as an optimal operating policy. It is the modeling sample cutoff that recorded the maximum simulated net benefit under the Base cost assumptions:

- Modeling sample cutoff: `Top 17%`
- Observed review count: `78,016`
- 20x weighted effective review count: `207,425`
- Effective review rate after 20x weighting: `45.20%` of the modeling sample count
- Simulated net benefit: `4,365.15`
- Cost assumptions: `EAD=1.0`, `LGD=0.5`, `intervention_effect=0.2`, `review_cost=0.01`, `friction_cost=0.005`

Observed precision and 20x weighted scenario precision are separated in all public result tables.

## How To Verify

```bash
python -m compileall src tests
python -m pytest tests -q -p no:cacheprovider
```

Full retraining requires the AMEX competition data, the integer parquet-formatted data, and enough compute for 5-fold LightGBM/XGBoost/CatBoost/MLP training. See [docs/reproduction_guide.md](docs/reproduction_guide.md).




