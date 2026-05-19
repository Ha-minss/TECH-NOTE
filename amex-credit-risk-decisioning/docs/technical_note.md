# Technical Note

## 1. Problem Definition

Default prediction scores are useful, but risk operations teams need a policy layer that converts scores into review priorities.

This project frames the AMEX score as a ranking-oriented decision support signal for manual review prioritization.

## 2. Original Modeling Pipeline

The original Colab experiment used AMEX customer-month parquet data and converted it into customer-level feature tables.

The feature engineering design included:

- customer history aggregation,
- missing-value indicators,
- recent change and ratio features,
- temporal movement features,
- model-ready customer-level score tables.

Multiple model families were explored, including LightGBM, XGBoost, CatBoost, MLP, and blended OOF scores.

## 3. Public Portfolio Scope

The public repository does not include the raw AMEX files or full training artifacts.

Instead, it focuses on the decisioning layer:

- masked score sample,
- risk decile validation,
- risk band monitoring,
- Top-K policy simulation,
- non-default downsampling correction,
- normalized cost-sensitive scenario analysis.

## 4. Top-K Policy Simulation

Customers are sorted by risk score and reviewed at fixed capacity thresholds.

The policy table compares:

- review queue size,
- observed defaults captured,
- non-default review workload,
- precision,
- capture rate,
- lift.

## 5. Weighted Correction

AMEX non-default examples are downsampled. To better reflect operating workload, non-default review counts are multiplied by 20.

This correction helps distinguish a policy that looks precise in the sampled dataset from one that may create large review workload in a broader population.

## 6. Cost-Sensitive Scenario Analysis

Normalized net benefit is calculated as:

```text
avoided_loss = TP * EAD * LGD * intervention_effect
review_cost_total = effective_review_count * review_cost
friction_cost_total = effective_fp * friction_cost
net_benefit = avoided_loss - review_cost_total - friction_cost_total
```

Because actual exposure, loss, revenue, and recovery data are unavailable, EAD is normalized to 1.

The Base scenario selects Top 17% as the strongest threshold, with normalized net benefit of 4,365.15.

## 7. Risk Bucket / Decile Validation

D1 is the highest-risk 10% and D10 is the lowest-risk 10%.

Observed results:

- D1 default rate: 96.59%
- D10 default rate: 0.04%

This monotonic separation supports the use of the score as a review-priority ranking signal.

## 8. Final Takeaway

A useful credit risk model does not end at prediction. It becomes valuable when its score is translated into a review-priority decisioning layer that can be monitored, audited, and improved.
