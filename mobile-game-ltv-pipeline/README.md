# Mobile Game LTV Pipeline

모바일 게임의 D0-D7 이벤트 로그를 사용해 D8-D180 LTV를 예측하고, 예측 결과를 단순 점수 제출이 아니라 **UA 예산 판단, 고가치 유저 우선순위, 모델 검증 리포트**까지 연결한 production-style ML pipeline입니다.

원본 데이터가 event log 형태이고, `user_id`만으로는 안정적인 모델링 단위가 되지 않는다는 점을 먼저 진단한 뒤, **모델링 grain 정의 → feature build → time-based validation → two-stage modeling → Optuna tuning → business report 로 구성했습니다.

---

## 1. Overview

모바일 게임 LTV 예측은 단순 회귀 문제가 아닙니다.

유저 대부분은 장기 매출이 0에 가깝고, 일부 고가치 유저가 전체 매출의 대부분을 차지합니다. 그래서 평균 오차만 줄이는 모델은 실제 UA 운영에서 충분하지 않습니다. 마케팅팀이 궁금한 것은 “모든 유저의 LTV를 조금 더 정확히 맞혔는가?”뿐만 아니라, **상위 고가치 유저와 고수익 세그먼트를 잘 찾아냈는가**입니다.

이 프로젝트는 D0-D7 초기 행동 로그를 기반으로 D8-D180 LTV를 예측합니다.

입력 데이터는 유저별 1행 데이터가 아니라 이벤트 로그입니다. train에는 약 2,100만 개 이벤트, test에는 약 519만 개 이벤트가 있고, 각 이벤트는 session, ad impression, IAP 같은 행동을 나타냅니다.

초기 EDA 결과, `user_id`만으로 groupby하면 같은 유저 안에서도 platform, country, channel, install_day, target이 섞이는 문제가 있었습니다. 그래서 단순 `user_id` 집계가 아니라, 다음 modeling grain을 사용했습니다.

```text
user_id + platform + country_tier + channel_tier + install_day
```

최종 모델은 `optuna_two_stage_top_capture`입니다.

구조는 다음과 같습니다.

```text
Stage 1: D8-D180 LTV가 0보다 클 확률 예측
Stage 2: 양수 LTV 유저의 log1p(LTV) 금액 예측
Final prediction = p_positive × predicted_ltv_if_positive
```

최종 holdout 결과는 다음과 같습니다.

| 지표 | 결과 |
|---|---:|
| MAE | 4.7472 |
| RMSE | 76.5951 |
| RMSLE | 0.5272 |
| Spearman correlation | 0.7970 |
| Top 10% revenue capture | 78.77% |
| Positive LTV rate in predicted top decile | 98.32% |

이 프로젝트의 결론은 다음과 같습니다.

> 모바일 게임 LTV 예측에서는 평균 오차만 보는 것이 아니라,  
> zero-inflated target, long-tail revenue, time-based validation, top-decile capture, UA 의사결정까지 함께 봐야 한다.

---

## 2. Problem & Objective

모바일 게임 UA에서는 설치 직후의 짧은 행동만 보고 장기 가치를 추정해야 합니다.

D0-D7 행동은 이미 관측할 수 있지만, D8-D180 LTV는 시간이 지나야 알 수 있습니다. 마케팅팀 입장에서는 장기 LTV를 기다린 뒤 예산을 조정하면 늦습니다. 초기에 어떤 유저와 세그먼트가 장기 매출을 만들 가능성이 높은지 빠르게 판단해야 합니다.

하지만 이 문제에는 여러 어려움이 있습니다.

| 문제 | 왜 어려운가 |
|---|---|
| Target이 zero-inflated | 많은 유저의 D8-D180 LTV가 0 |
| Long-tail revenue | 일부 고가치 유저가 전체 매출 대부분을 차지 |
| Event-level raw data | 원본은 유저 1행이 아니라 D0-D7 이벤트 로그 |
| User grain 불안정 | `user_id`만으로 묶으면 context와 target이 충돌 |
| Train/test submission grain 불일치 | context-level 예측을 user-level 제출로 변환해야 함 |
| 실제 CPI 없음 | ROAS 판단은 실제 비용이 아니라 simulation으로 제한해야 함 |
| 리더보드 점수만으로 부족 | UA 의사결정에서는 top user capture와 segment 판단이 중요 |

따라서 이 프로젝트의 목표는 단순히 예측 모델 하나를 만드는 것이 아닙니다.

목표는 다음과 같습니다.

첫째, raw event log를 안정적인 modeling grain으로 변환합니다.

둘째, D0-D7 행동을 기반으로 장기 LTV 예측 feature를 만듭니다.

셋째, zero-heavy target에 맞게 single-stage model과 two-stage model을 비교합니다.

넷째, time-based validation과 rolling validation으로 모델이 시간축에서 안정적인지 확인합니다.

다섯째, RMSLE뿐 아니라 top 10% revenue capture를 함께 평가합니다.

여섯째, 최종 예측을 UA segment decision simulation과 business report로 연결합니다.

---

## 3. Data

원본 데이터는 D0-D7 기간의 event-level 로그입니다.

| 항목 | Train | Test |
|---|---:|---:|
| Event rows | 21,006,238 | 5,192,340 |
| Unique `user_id` | 75,464 | 31,399 |
| Rows/user median | 32 | 9 |
| Rows/user p95 | 1,166 | 860 |
| Rows/user max | 178,821 | 96,075 |

이벤트 유형 분포는 다음과 같습니다.

| Event type | Train rows | Train share | Test rows | Test share |
|---|---:|---:|---:|---:|
| `ad_impression` | 18,590,666 | 88.50% | 4,618,468 | 88.95% |
| `session` | 2,359,512 | 11.23% | 558,644 | 10.76% |
| `iap` | 56,060 | 0.27% | 15,228 | 0.29% |

Target은 `ltv_d8_d180`입니다.

모델 입력 검증 기준 target 분포는 다음과 같습니다.

| 항목 | 값 |
|---|---:|
| Rows | 159,521 |
| Positive LTV rate | 40.45% |
| Zero LTV rate | 59.55% |
| Mean | 18.9218 |
| P50 | 0.0000 |
| P75 | 1.2754 |
| P95 | 20.2234 |
| P99 | 279.9575 |
| Max | 62,046.4734 |

EDA에서 가장 중요한 발견은 `user_id`만으로는 안정적인 모델링 단위가 아니라는 점이었습니다.

| Grain | Train groups | Target collision groups | Collision rate |
|---|---:|---:|---:|
| `user_id` | 75,464 | 34,191 | 45.31% |
| `user_id + install_day` | 146,129 | 6,953 | 4.76% |
| `user_id + platform + country_tier + channel_tier + install_day` | 159,926 | 405 | 0.25% |

`user_id` 기준으로 묶으면 target collision group이 34,191개, collision rate가 45.31%였습니다. 즉, 같은 `user_id` 안에서 서로 다른 context나 target이 섞일 수 있었습니다.

그래서 최종 modeling grain은 다음으로 고정했습니다.

```text
user_id + platform + country_tier + channel_tier + install_day
```

남은 405개 target-collision group은 supervised training에서 제외하고 `dropped_collision_groups.csv`에 기록했습니다.

---

## 4. Method / System Design

이 프로젝트의 설계 원칙은 다음과 같습니다.

> 먼저 데이터 단위를 검증하고,  
> 그 다음 feature를 만들고,  
> 마지막에 모델을 선택한다.

전체 pipeline은 다음과 같습니다.

```text
Raw competition zip
   ↓
Raw data validation
   ↓
Modeling grain diagnostics
   ↓
Feature build
   ↓
Model input validation
   ↓
Baseline / Linear / XGBoost experiments
   ↓
Two-stage model experiment
   ↓
Rolling time validation
   ↓
Optuna tuning
   ↓
Final two-stage refit
   ↓
Prediction artifact generation
   ↓
Business analysis report
   ↓
Model card
```

### 4.1 Modeling Grain

처음에는 `user_id` 단위 LTV 예측 문제처럼 보입니다.

하지만 EDA 결과 `user_id` 내부에서 platform, country, channel, install_day가 바뀌는 사례가 많았습니다. 그래서 `user_id`만으로 feature를 집계하면 서로 다른 설치 context가 섞이고, label도 충돌할 수 있습니다.

최종 grain은 다음입니다.

```text
user_id + platform + country_tier + channel_tier + install_day
```

이 grain은 target collision rate를 45.31%에서 0.25%로 낮췄습니다.

### 4.2 Feature Engineering

D0-D7 이벤트 로그를 grain 단위 feature로 변환했습니다.

Feature는 크게 다음 그룹으로 나눌 수 있습니다.

| Feature group | 예시 | 의미 |
|---|---|---|
| Activity | `event_count`, `session_count`, `active_days`, `last_event_day` | 초기 활동성 |
| Ad behavior | `ad_impression_count`, `ads_per_session`, `ad_revenue_per_ad` | 광고 소비와 광고 수익성 |
| Early revenue | `revenue_d0_d7`, `ad_revenue_d0_d7`, `iap_revenue_d0_d7` | 초기 매출 신호 |
| Time bucket | `revenue_d0`, `revenue_d1`, `revenue_d2_d3`, `revenue_d4_d7` | 초반/후반 매출 변화 |
| IAP behavior | `iap_count`, `avg_iap_amount`, `max_iap_amount`, `unique_product_count` | 결제 행동 |
| Context | `platform`, `country_tier`, `channel_tier`, `install_day` | 유입 환경 |
| Target encoding | `te_platform_country_channel_ltv_log_mean` 등 | segment-level prior |

Feature build 결과는 다음과 같습니다.

| 항목 | 결과 |
|---|---:|
| Train feature rows | 159,521 |
| Test feature rows | 40,105 |
| Dropped target-collision groups | 405 |
| Train feature columns | 40 |
| Test feature columns | 39 |

### 4.3 Two-stage Modeling

LTV target은 0이 많고, 양수 LTV 안에서도 long-tail이 큽니다.

그래서 최종 모델은 두 단계로 나누었습니다.

| Stage | 역할 |
|---|---|
| Stage 1 classifier | D8-D180 LTV가 0보다 클 확률 예측 |
| Stage 2 regressor | 양수 LTV 유저의 `log1p(LTV)` 금액 예측 |
| Final prediction | `p_positive × predicted_ltv_if_positive` |

이 구조의 장점은 zero-heavy target을 분리해서 다룰 수 있다는 점입니다.

단일 회귀 모델은 0 유저와 고가치 유저를 동시에 맞히려 하면서 예측이 평균으로 눌릴 수 있습니다. Two-stage 구조는 “양수 LTV가 될 가능성”과 “양수라면 얼마나 클지”를 나누어 모델링합니다.

### 4.4 Time-based Validation

이 프로젝트는 random KFold를 중심으로 평가하지 않았습니다.

모바일 게임 LTV 예측은 install_day 기준으로 시간 흐름이 있기 때문에, 미래 유저를 예측하는 상황과 비슷하게 validation을 구성해야 합니다.

Primary holdout split은 다음입니다.

```text
Train: install_day 0-23
Valid: install_day 24-30
```

추가로 expanding rolling validation을 수행했습니다.

| Fold | Train days | Valid days | Train rows | Valid rows |
|---:|---|---|---:|---:|
| 1 | 0-13 | 14-16 | 81,185 | 14,186 |
| 2 | 0-16 | 17-19 | 95,371 | 13,825 |
| 3 | 0-19 | 20-23 | 109,196 | 18,254 |
| 4 | 0-23 | 24-30 | 127,450 | 32,071 |

Target encoding은 각 fold의 train row에서만 fit하고 valid row에 map했습니다. p1/p99 clipping과 preprocessing도 fold train 기준으로만 만들었습니다.

---

## 5. Implementation

이 프로젝트는 실험 notebook이 아니라 `make all`로 재현 가능한 pipeline 형태로 구성했습니다.

`make all`은 최종 선택 모델 실행에 필요한 단계만 수행합니다.

```text
1. raw data validation
2. feature build
3. model input validation
4. final two-stage model train/refit
5. prediction artifact generation
6. business analysis report generation
7. model card generation
```

실험용 baseline, linear model, feature ablation, rolling validation, Optuna tuning은 최종 pipeline과 분리했습니다. 이 실험들은 모델 선택 근거로 보존하고, 필요할 때 `make experiments`로 재현할 수 있습니다.

주요 모듈은 다음과 같습니다.

| 모듈 | 역할 | 쉽게 말하면 |
|---|---|---|
| `validate_raw_data.py` | raw train/test event log 검증 | 입력 데이터 이상 여부 확인 |
| `build_features.py` | modeling grain feature 생성 | event log를 모델 입력으로 변환 |
| `validate_model_input.py` | train/test feature schema 검증 | 모델에 넣기 전 null/inf/schema 확인 |
| `train_final_model.py` | 최종 two-stage model refit | 선택된 모델을 전체 train에 재학습 |
| `predict_submission.py` | test prediction 생성 | context-level 예측을 user-level로 집계 |
| `build_business_report.py` | business analysis 생성 | top decile, UA simulation, feature importance |
| `run_experiments.py` | 모델 선택 실험 재현 | baseline부터 Optuna까지 선택 실험 실행 |
| `common/metrics.py` | 평가 지표 | RMSLE, Spearman, top capture 등 |
| `common/preprocessing.py` | 전처리 | clipping, categorical encoding 등 |
| `common/target_encoding.py` | target encoding | leakage 방지형 segment encoding |

모델 입력 검증 결과는 다음과 같습니다.

| 항목 | 결과 |
|---|---|
| Train/test feature columns match | True |
| Target exists in train | True |
| Target exists in test | False |
| Train duplicate grain rows | 0 |
| Test duplicate grain rows | 0 |
| Post-preprocessing numeric null | 0 |
| Post-preprocessing categorical null | 0 |
| Time split possible | True |

---

## 6. Evaluation

평가는 세 가지 층으로 나누었습니다.

첫째, 데이터와 feature가 모델 학습 가능한 구조인지 검증했습니다.

둘째, baseline부터 최종 모델까지 단계적으로 성능을 비교했습니다.

셋째, UA 운영 관점에서 상위 유저와 세그먼트를 얼마나 잘 찾아내는지 확인했습니다.

---

### 6.1 Baseline → Linear → XGBoost

먼저 단순 baseline과 linear model을 만들고, 이후 XGBoost를 추가했습니다.

| Model | MAE | RMSE | RMSLE | Spearman | Top 10% revenue capture |
|---|---:|---:|---:|---:|---:|
| `global_mean` | 24.1797 | 104.0161 | 2.7500 | 0.0000 | 6.51% |
| `segment_mean` | 16.6481 | 105.0316 | 2.0948 | 0.1139 | 17.15% |
| `early_revenue_multiplier` | 10.2615 | 169.3231 | 0.9160 | 0.7235 | 72.06% |
| `ridge_log_linear` | 6.2176 | 97.1298 | 0.6645 | 0.7686 | 74.08% |
| `xgboost_log_target` | 5.1163 | 83.4851 | 0.5476 | 0.8031 | 76.32% |

이 결과는 초기 D0-D7 revenue가 강한 baseline이라는 점을 보여줍니다. 단순 early revenue multiplier만으로도 top 10% revenue capture가 72.06%였습니다.

하지만 XGBoost는 비선형 활동성, 광고 노출, IAP, context feature를 함께 사용하면서 RMSLE와 ranking 성능을 모두 개선했습니다.

---

### 6.2 Feature Engineering Experiment

XGBoost 기준으로 feature set을 추가 비교했습니다.

| Feature set | MAE | RMSE | RMSLE | Spearman | Top 10% revenue capture |
|---|---:|---:|---:|---:|---:|
| `xgb_current_full` | 5.1163 | 83.4851 | 0.5476 | 0.8031 | 76.32% |
| `xgb_time_bucket_features` | 5.1355 | 84.1380 | 0.5447 | 0.8025 | 76.57% |
| `xgb_velocity_ratio_features` | 5.1225 | 82.5995 | 0.5456 | 0.8032 | 76.60% |
| `xgb_frequency_interaction_features` | 5.0886 | 83.7111 | 0.5430 | 0.8031 | 76.49% |
| `xgb_target_encoding_features` | 5.0878 | 83.7934 | 0.5404 | 0.8023 | 76.41% |

Target encoding feature set은 RMSLE 기준으로 가장 좋았습니다. 다만 top 10% revenue capture만 보면 velocity/time bucket 계열도 비슷하게 작동했습니다.

따라서 이후 모델 선택에서는 RMSLE와 top capture를 함께 봤습니다.

---

### 6.3 Two-stage Model

Zero-heavy target을 반영하기 위해 two-stage XGBoost를 실험했습니다.

| Model | MAE | RMSE | RMSLE | Spearman | Top 10% revenue capture | Top-decile lift |
|---|---:|---:|---:|---:|---:|---:|
| `xgb_target_encoding_features` | 5.0878 | 83.7934 | 0.5404 | 0.8023 | 76.41% | 7.64 |
| `two_stage_xgb_target_encoding_features` | 5.0390 | 80.2077 | 0.5447 | 0.8051 | 77.66% | 7.76 |

Two-stage model은 best single-stage RMSLE보다 약간 나빴지만, top 10% revenue capture는 더 좋았습니다.

즉, 평균적인 log error만 보면 single-stage가 유리하고, 고가치 유저를 상위로 올리는 ranking 관점에서는 two-stage가 유리했습니다.

이 프로젝트는 UA 의사결정 관점에서 top-decile capture를 중요하게 봤기 때문에 two-stage 계열을 최종 후보로 유지했습니다.

---

### 6.4 Rolling Time Validation

Rolling validation에서는 RMSLE 안정성과 top-decile capture 안정성을 분리해서 봤습니다.

| Model | RMSLE mean | RMSLE std | Top 10% capture mean | Top 10% capture std | Spearman mean |
|---|---:|---:|---:|---:|---:|
| `single_stage_xgb_target_encoding_features` | 0.5349 | 0.0157 | 78.76% | 2.32% | 0.7961 |
| `single_stage_xgb_velocity_ratio_features` | 0.5400 | 0.0169 | 78.52% | 2.10% | 0.7955 |
| `two_stage_xgb_target_encoding_features` | 0.5409 | 0.0120 | 79.77% | 2.62% | 0.7979 |
| `two_stage_xgb_velocity_ratio_features` | 0.5438 | 0.0132 | 79.16% | 2.06% | 0.7971 |

해석은 명확합니다.

| 관점 | 가장 좋은 후보 |
|---|---|
| RMSLE mean | `single_stage_xgb_target_encoding_features` |
| Top 10% capture mean | `two_stage_xgb_target_encoding_features` |

즉, 최종 모델 선택은 단순히 RMSLE 1등을 고르는 문제가 아니었습니다.

UA 운영에서는 상위 유저 포착이 중요하기 때문에, top capture objective를 별도로 고려했습니다.

---

### 6.5 Optuna Tuning and Final Model

Optuna는 rolling validation에서 좁혀진 후보만 대상으로 수행했습니다.

| 항목 | 설정 |
|---|---|
| Trials per study | 30 |
| Early stopping rounds | 50 |
| Tuning folds | install_day 0-13 → 14-16, 0-16 → 17-19, 0-19 → 20-23 |
| Final holdout | install_day 0-23 → 24-30 |
| Feature set | target encoding features |
| Leakage control | target encoding은 fold train에서만 fit |

최종 holdout 결과는 다음과 같습니다.

| Model | Objective | MAE | RMSE | RMSLE | Spearman | Top 10% revenue capture | Top-decile lift |
|---|---|---:|---:|---:|---:|---:|---:|
| `optuna_single_stage_rmsle` | RMSLE | 4.9102 | 80.5268 | 0.5307 | 0.8004 | 76.93% | 7.69 |
| `optuna_two_stage_top_capture` | Top capture | 4.7472 | 76.5951 | 0.5272 | 0.7970 | 78.77% | 7.88 |

최종 선택 모델은 `optuna_two_stage_top_capture`입니다.

선택 이유는 다음과 같습니다.

| 기준 | 해석 |
|---|---|
| MAE/RMSE | single-stage tuned model보다 낮음 |
| RMSLE | 0.5272로 single-stage tuned model보다도 낮음 |
| Top 10% revenue capture | 78.77%로 가장 높음 |
| Top-decile lift | 7.88로 가장 높음 |
| Business fit | UA 운영에서 고가치 유저 우선순위에 적합 |

---

### 6.6 Top-Decile Business Analysis

최종 모델이 예측한 상위 10% 유저는 validation row의 10.00%, 3,208명입니다.

이 상위 10%가 실제 D8-D180 revenue의 78.77%를 포착했습니다.

상위 10%와 나머지 유저의 행동 차이는 다음과 같습니다.

| Feature | Top decile mean | Non-top mean | Ratio |
|---|---:|---:|---:|
| `iap_revenue_d0_d7` | 15.3444 | 0.2520 | 60.90 |
| `revenue_d0_d7` | 17.5543 | 0.5012 | 35.02 |
| `revenue_per_active_day` | 4.3845 | 0.1728 | 25.37 |
| `early_payer_flag` | 0.1428 | 0.0158 | 9.04 |
| `ad_revenue_d0_d7` | 2.2098 | 0.2492 | 8.87 |
| `ad_impression_count` | 574.6328 | 73.4238 | 7.83 |
| `event_count` | 586.4177 | 90.5853 | 6.47 |
| `active_days` | 6.8974 | 3.1880 | 2.16 |

Top-decile 유저는 단순히 이벤트가 많은 유저가 아닙니다.

초기 IAP revenue, 전체 초기 revenue, revenue per active day, early payer 여부가 매우 강한 차이를 보였습니다. 즉, 모델은 “활동이 많은 유저”뿐 아니라 “초기 monetization quality가 높은 유저”를 상위로 올리고 있습니다.

---

### 6.7 UA Decision Simulation

최종 예측값을 country/channel segment 단위로 묶고, synthetic CPI를 붙여 predicted ROAS 기반 의사결정 simulation을 만들었습니다.

중요한 점은 synthetic CPI가 실제 광고비가 아니라는 것입니다. 이 table은 실제 예산 집행 결과가 아니라, LTV 예측값을 UA decision workflow로 연결하는 예시입니다.

메인 table은 `min_users=100` 이상 segment만 decision을 부여했습니다.

| Country | Channel | Users | Predicted LTV | Actual LTV | Synthetic CPI | Predicted ROAS | Actual ROAS | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---|
| NL | `bb16a88d` | 141 | 38.9756 | 61.6187 | 0.8075 | 48.27 | 76.31 | `scale_up` |
| ES | `92247aa9` | 108 | 22.7146 | 77.0867 | 0.8075 | 28.13 | 95.46 | `scale_up` |
| TR | `bb16a88d` | 115 | 18.5414 | 53.4072 | 0.8075 | 22.96 | 66.14 | `scale_up` |
| IT | `bb16a88d` | 128 | 12.4819 | 18.1852 | 0.8075 | 15.46 | 22.52 | `scale_up` |
| PL | `92247aa9` | 301 | 11.2661 | 12.3424 | 0.8075 | 13.95 | 15.28 | `scale_up` |

표본 수가 작은 segment는 `insufficient_sample`로 분리했습니다.

예를 들어 `OTHER + 0a0ae9c4`는 predicted ROAS가 81.10으로 매우 높아 보이지만, users가 71명이라 scale decision을 주지 않았습니다.

이 점이 중요합니다.

> 예측 ROAS가 높아 보여도 표본 수가 작으면 바로 scale-up하면 안 된다.  
> LTV model output은 budget decision으로 바꾸기 전에 sample-size guardrail을 거쳐야 한다.

---

## 7. Key Design Decisions

### 7.1 `user_id`가 아니라 user-context grain을 사용했다

처음에는 유저별 LTV 예측이므로 `user_id`로 묶으면 될 것처럼 보였습니다.

하지만 EDA 결과 `user_id` 기준 target collision rate가 45.31%였습니다. 같은 `user_id` 안에 서로 다른 platform, country, channel, install_day가 섞여 있었고, target도 일관되지 않았습니다.

그래서 `user_id + platform + country_tier + channel_tier + install_day`를 modeling grain으로 선택했습니다. 이 결정이 없었다면 이후 모델 성능은 좋아 보여도 label 정의가 흔들렸을 가능성이 큽니다.

### 7.2 남은 target collision group은 평균내지 않고 제거했다

Composite grain을 사용해도 405개 collision group이 남았습니다.

이를 target 평균으로 처리할 수도 있었지만, 그러면 identity 문제가 모델 학습 안에 숨어버립니다. 그래서 첫 supervised training에서는 해당 group을 제거하고, 별도 log로 남겼습니다.

### 7.3 Random KFold보다 time-based validation을 사용했다

LTV 예측은 미래 설치 유저를 예측하는 문제입니다.

따라서 random split으로 과거와 미래가 섞이면 실제 운영 상황보다 낙관적인 성능이 나올 수 있습니다. 그래서 install_day 기준 holdout과 rolling validation을 사용했습니다.

### 7.4 RMSLE와 top-decile capture를 함께 봤다

RMSLE는 전체 예측 오차를 보는 데 유용하지만, UA 운영에서는 상위 가치 유저를 잘 찾는지도 중요합니다.

그래서 RMSLE, MAE, RMSE, Spearman뿐 아니라 top 10% revenue capture와 top-decile lift를 함께 봤습니다.

### 7.5 Two-stage model을 최종 후보로 유지했다

Zero-heavy target에서는 “LTV가 0인지 아닌지”와 “양수라면 얼마나 큰지”가 다른 문제입니다.

Two-stage model은 이 둘을 분리해 모델링합니다. 최종 Optuna 결과에서 two-stage model은 RMSLE와 top capture 모두 강하게 나왔기 때문에 최종 모델로 선택했습니다.

### 7.6 UA simulation에는 sample-size guardrail을 넣었다

Segment별 predicted ROAS가 높아도 표본 수가 너무 작으면 실제 예산 판단에 쓰기 어렵습니다.

그래서 `min_users=100` 기준을 두고, 작은 segment는 `insufficient_sample`로 분리했습니다.

### 7.7 최종 pipeline과 실험 pipeline을 분리했다

`make all`은 최종 재현 가능한 pipeline만 실행합니다.

baseline, feature ablation, rolling validation, Optuna는 `make experiments`로 따로 재현하도록 분리했습니다. 이렇게 해야 최종 실행은 빠르고 명확하며, 실험 근거는 별도 report로 유지할 수 있습니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 일반적인 Kaggle LTV 회귀 문제처럼 보였습니다.

하지만 EDA를 진행하면서 가장 중요한 문제는 모델 알고리즘이 아니라 **모델링 단위가 무엇인가**라는 점이었습니다. `user_id`만으로 묶으면 target collision이 너무 컸고, 이 상태에서 모델링을 하면 성능 수치가 나와도 해석하기 어려웠습니다.

첫 번째 전환점은 modeling grain 결정이었습니다. `user_id + platform + country_tier + channel_tier + install_day`를 사용하면서 target collision rate를 45.31%에서 0.25%까지 줄였습니다.

두 번째 전환점은 평가 지표였습니다. early revenue multiplier baseline이 이미 top 10% revenue capture 72.06%를 기록했습니다. 즉, 단순 모델도 꽤 강한 ranking signal을 갖고 있었습니다. 그래서 모델 비교를 RMSLE 하나로만 하면 부족하다고 판단했습니다.

세 번째 전환점은 two-stage modeling이었습니다. LTV target은 0이 많고 long-tail이 강합니다. 그래서 양수 여부와 양수 금액을 나누어 모델링했고, 최종적으로 top capture objective와 잘 맞았습니다.

네 번째 전환점은 business report였습니다. 모델 결과를 submission score로 끝내지 않고, predicted top decile profile과 UA decision simulation까지 연결했습니다. 특히 synthetic CPI는 실제 광고비가 아니라 workflow demonstration임을 명확히 표시했습니다.

결과적으로 이 프로젝트는 “모델 하나 훈련한 notebook”이 아니라, **데이터 계약, 모델링 단위 검증, 모델 선택 근거, 운영 리포트가 포함된 ML pipeline**으로 정리되었습니다.

---

## 9. Limitations

이 프로젝트는 portfolio용 production-style pipeline이며, 실제 게임 UA 운영에 바로 적용하려면 추가 데이터와 검증이 필요합니다.

첫째, 실제 CPI, 캠페인 예산, creative, bid, country별 media cost가 없습니다. 따라서 UA decision simulation은 실제 예산 추천이 아니라 workflow 예시입니다.

둘째, test label이 없으므로 hidden test MAE/RMSE/RMSLE는 계산할 수 없습니다. Test prediction report는 row count, non-null, non-negative, fallback count 같은 제출 검증 중심입니다.

셋째, modeling grain은 가장 방어적인 선택이지만 완벽하지 않습니다. 남은 405개 target collision group은 제거했으며, 실제 운영에서는 identity stitching이나 attribution 기준 확인이 필요합니다.

넷째, 최종 모델은 D0-D7 관측 데이터만 사용합니다. 실제 운영에서는 D1/D3/D7 시점별로 다른 early prediction model을 운영할 수 있습니다.

다섯째, 현재 모델은 XGBoost 중심입니다. 더 큰 운영 환경에서는 calibration, drift monitoring, retraining schedule, online/offline feature consistency가 필요합니다.

여섯째, top-decile capture는 UA ranking에 유용하지만, budget allocation은 실제 CPI, marginal ROAS, campaign saturation, creative fatigue와 함께 판단해야 합니다.

---

## 10. How to Run

### Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Raw competition data는 git에 포함하지 않습니다.

기본 zip 경로는 다음입니다.

```text
%USERPROFILE%/Downloads/mobile-game-ltv-forecasting-challenge.zip
```

다른 경로를 사용할 경우 `ZIP_PATH`를 지정합니다.

```bash
make all ZIP_PATH=/path/to/mobile-game-ltv-forecasting-challenge.zip
```

### Run final pipeline

```bash
make all
```

`make all`은 최종 two-stage LTV pipeline만 실행합니다.

```text
validate → features → train → predict → business
```

### Run individual steps

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

| Command | 역할 |
|---|---|
| `make validate` | raw train/test event log 검증 |
| `make features` | modeling grain feature와 model input 생성 |
| `make train` | 최종 two-stage model refit |
| `make predict` | test prediction과 submission 생성 |
| `make business` | model card와 business analysis 생성 |
| `make test` | unit test 실행 |
| `make experiments` | baseline, linear, XGBoost, rolling, Optuna 실험 재현 |
| `make clean` | 최종 pipeline 산출물 정리 |

---

## 11. Project Structure

```text
mobile-game-ltv-pipeline/
├── README.md
├── Makefile
├── requirements.txt
├── data/
│   ├── processed/
│   │   ├── train_model_input.parquet
│   │   ├── test_model_input.parquet
│   │   ├── final_model_metrics.csv
│   │   ├── final_model_params.json
│   │   ├── final_holdout_predictions.parquet
│   │   ├── top_decile_analysis.csv
│   │   ├── ua_decision_simulation.csv
│   │   └── model_input_validation.json
│   └── experiments/
│       ├── baseline_metrics.csv
│       ├── linear_model_metrics.csv
│       ├── xgboost_model_metrics.csv
│       ├── two_stage_metrics.csv
│       ├── rolling_validation_metrics.csv
│       ├── optuna_best_metrics.csv
│       ├── submission.csv
│       └── test_predictions.csv
├── models/
│   ├── final_two_stage_stage1.joblib
│   ├── final_two_stage_stage2.joblib
│   └── final_preprocessor.joblib
├── reports/
│   ├── final_model_card.md
│   ├── business_analysis.md
│   ├── model_selection_summary.md
│   ├── diagnostics/
│   ├── eda/
│   └── experiments/
├── scripts/
│   ├── eda_profile.py
│   └── grain_diagnostics.py
├── src/
│   ├── common/
│   ├── experiments/
│   └── pipeline/
└── tests/
```

---

## 12. What This Project Demonstrates

이 프로젝트는 모바일 게임 LTV 예측을 단순 regression notebook이 아니라, 재현 가능한 ML pipeline과 business-facing model report로 구성한 사례입니다.

첫째, event-level raw data에서 안정적인 modeling grain을 먼저 검증했습니다.

둘째, `user_id` 기준 target collision 문제를 발견하고, user-context grain을 선택해 collision rate를 45.31%에서 0.25%로 줄였습니다.

셋째, D0-D7 activity, ad behavior, IAP, revenue timing, context, target encoding feature를 생성했습니다.

넷째, baseline, linear model, XGBoost, two-stage XGBoost, rolling validation, Optuna tuning을 단계적으로 비교했습니다.

다섯째, random KFold 대신 install_day 기반 time validation과 rolling validation을 사용했습니다.

여섯째, zero-inflated LTV target을 반영해 positive probability와 conditional positive value를 분리한 two-stage model을 최종 선택했습니다.

일곱째, RMSLE뿐 아니라 top 10% revenue capture, top-decile lift, Spearman correlation을 함께 평가했습니다.

여덟째, 최종 모델은 holdout에서 RMSLE 0.5272, Top 10% revenue capture 78.77%, Top-decile lift 7.88을 기록했습니다.

아홉째, predicted top-decile behavior와 UA decision simulation을 만들어 모델 결과를 마케팅 의사결정 형태로 번역했습니다.

마지막으로, `make all`로 raw validation부터 feature build, model refit, prediction, business report까지 재현 가능한 pipeline을 구성했습니다.

이 프로젝트의 핵심은 단순히 LTV 예측 모델을 만든 것이 아니라, **데이터 grain 검증, 모델 선택 근거, ranking-oriented evaluation, UA 의사결정 연결까지 포함한 production-style LTV pipeline을 설계한 것**입니다.
