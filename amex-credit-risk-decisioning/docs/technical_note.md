# Technical Note

## 1. Problem Definition

AMEX default prediction score를 review priority로 바꾸는 decisioning layer를 설계했다.

## 2. Preprocessing

원자료 단위는 customer-month이다. 모델 입력은 customer-level table이므로 월별 이력을 고객 단위 feature로 집계했다.

Feature layer:

- Base: last, first, mean, std, min, max, sum, median, count
- Change: last - mean, last - first, last / mean, last / first
- Temporal: last - lag1, last - lag3, last - lag6, recent 3-month and 6-month statistics
- Missing: missing count, missing ratio, variable-level missing flags
- Categorical: last, first, nunique, mode

## 3. Modeling

여러 모델 계열의 OOF score를 만들고 final ranking score로 결합했다.

Model families:

- LightGBM
- XGBoost
- CatBoost
- LightGBM Top-N feature subsets
- Recent-change LightGBM
- Tabular MLP
- Ridge meta model
- Equal blend

Final model version: `best_equal_8models`

## 4. Validation

Score validation은 calibrated probability가 아니라 ranking quality에 초점을 둔다.

- D1 default rate: 96.59%
- D10 default rate: 0.04%

상위 risk decile에 default가 강하게 집중되어 review priority score로 사용할 수 있다.

## 5. Scenario

Top-K review policy를 비교하고, AMEX downsampling 구조를 반영하기 위해 non-default workload를 20배 보정했다.

Base scenario에서 Top 17%가 가장 높은 normalized net benefit을 보였다.

## 6. Limitation

Normalized net benefit은 실제 손익이 아니다. customer-level exposure, recovery, revenue, credit limit이 없기 때문에 정책 비교용 지표로만 해석한다.
