# Mobile Game LTV Production-Style ML Pipeline

This repository is a portfolio project for a production-style mobile game LTV prediction pipeline. It focuses on the parts a machine learning engineer is expected to handle in practice: data contracts, defensible modeling grain, reproducible feature generation, model-input validation, final model refit, prediction artifacts, model reporting, and business-facing analysis.

The project is not positioned as a leaderboard-only Kaggle notebook. The raw data is an event log, and EDA showed that `user_id` alone is not a reliable modeling grain. The final training dataset therefore uses a validated user-context grain.


## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Raw competition data is expected outside git. By default the Makefile reads:

```text
%USERPROFILE%/Downloads/mobile-game-ltv-forecasting-challenge.zip
```

You can override it with:

```bash
make all ZIP_PATH=/path/to/mobile-game-ltv-forecasting-challenge.zip
```

## Main Command

```bash
make all
```

`make all` runs only the final two-stage LTV pipeline:

1. raw data validation
2. feature build
3. model input validation
4. final two-stage model train/refit
5. validation/test-like prediction artifact generation
6. business analysis report generation
7. model card generation

It does not run baseline, linear models, feature ablation, rolling validation, or Optuna tuning. Those experiments are retained as model-selection evidence and can be reproduced separately with `make experiments`.

## Make Targets

```bash
make validate
make features
make train
make predict
make business
make test
make experiments
make clean
```

- `make validate`: validate raw train/test event logs and write diagnostics under `reports/diagnostics/`.
- `make features`: build modeling-grain feature tables and model-ready inputs.
- `make train`: refit the selected final two-stage XGBoost model on all labeled training rows using `data/processed/final_model_params.json`.
- `make predict`: generate final prediction artifacts without calculating hidden-test metrics.
- `make business`: generate the final model card and business analysis reports.
- `make test`: run the unit test suite.
- `make experiments`: optional reproduction of model-selection experiments.
- `make clean`: remove generated final-pipeline prediction/model artifacts.

## Data Contract

The raw files are D0-D7 event logs, not one-row-per-user tables. The validated modeling grain is:

```text
user_id + platform + country_tier + channel_tier + install_day
```

This grain was selected because `user_id` alone showed context and target consistency problems during EDA. Residual target-collision groups are removed from supervised training and logged.

## Final Model

The selected model is:

```text
optuna_two_stage_top_capture
```

It uses a two-stage structure:

```text
Stage 1: P(ltv_d8_d180 > 0)
Stage 2: E(log1p(ltv_d8_d180) | positive LTV)
Final prediction: p_positive * predicted_ltv_if_positive
```

The final refit uses all labeled train rows. Test metrics are not calculated because test labels are unavailable.

## Repository Layout

```text
src/pipeline/      final runnable pipeline code
src/experiments/   optional model-selection experiments
src/common/        shared metrics, preprocessing, target encoding, and IO helpers
data/processed/    final pipeline artifacts and selected final-model inputs
data/experiments/  baseline/linear/XGBoost/two-stage/Optuna experiment outputs
reports/           final model card and business reports
reports/diagnostics/ raw data, grain, missingness, and model-input diagnostics
reports/experiments/ model-selection experiment reports
models/            final refit model artifacts
```

## Key Final Outputs

```text
data/processed/train_model_input.parquet
data/processed/test_model_input.parquet
data/processed/final_model_params.json
data/processed/final_model_metrics.csv
data/processed/final_holdout_predictions.parquet
data/processed/final_test_context_predictions.parquet
data/processed/final_test_user_predictions.parquet
models/final_two_stage_stage1.joblib
models/final_two_stage_stage2.joblib
models/final_preprocessor.joblib
reports/final_prediction_report.md
reports/final_model_card.md
reports/business_analysis.md
```

## Model Selection Evidence

See [`reports/model_selection_summary.md`](reports/model_selection_summary.md) for links to the retained baseline, linear, XGBoost, feature engineering, rolling validation, and Optuna evidence.
