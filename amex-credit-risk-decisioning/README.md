# 카드사는 누구를 먼저 검토해야 하는가?

신용카드 상환 불이행 위험 예측 점수를 **리스크팀의 월별 리뷰 우선순위, Top-K 검토 정책, 비용 민감도 시뮬레이션**으로 전환한 Credit Risk Decisioning 프로젝트입니다.

이 프로젝트는 “누가 default할까?”를 맞히는 데서 끝나지 않습니다. 고객별 위험 점수를 만들고, 이를 제한된 리뷰 인력 안에서 **이번 달 누구를 먼저 검토해야 하는가**라는 운영 의사결정 문제로 바꿉니다.

---

## 1. Overview

신용카드 리스크팀의 문제는 단순히 “누가 불이행할 것인가”를 맞히는 것이 아닙니다.

실제 운영에서는 모든 고객을 매월 자세히 검토할 수 없습니다. 제한된 검토 인력 안에서 이번 달 누구를 먼저 보고, 어느 구간까지 개입할지 결정해야 합니다.

이 위험을 제대로 보지 못하면 신용손실이 커질 수 있고, 반대로 지나치게 보수적으로 관리하면 실제로는 정상 상환할 고객까지 불필요하게 검토하게 되어 고객 경험과 영업 기회를 해칠 수 있습니다.

본 프로젝트는 American Express 공개 데이터를 활용해 신용카드 상환 불이행 위험 점수를 만들고, 이를 리뷰 우선순위 구조로 전환합니다.

핵심 질문은 다음과 같습니다.

> 신용카드 상환 불이행 위험 점수를 만들었을 때,  
> 리스크팀은 이번 달 누구를 먼저 검토해야 하는가?

최종 모델 점수는 고객별 절대 부도확률을 단정하기 위한 값이라기보다, 제한된 리뷰 자원 안에서 위험 고객을 상위에 배치하기 위한 **ranking-oriented risk score**로 해석했습니다.

주요 결과는 다음과 같습니다.

위험 점수 상위 10% 구간은 관측된 불이행 고객의 37.30%를 포착했고, Lift는 3.73이었습니다. 상위 20%까지 넓히면 Capture Rate는 68.31%까지 올라가지만, 정상 고객 검토 부담도 크게 증가했습니다.

비용 민감도 시뮬레이션에서는 기준 가정에서 Top 17% 리뷰 정책이 가장 높은 정규화 순효익을 보였습니다. 하지만 Conservative 시나리오에서는 Top 4%, Aggressive 시나리오에서는 Top 28%가 가장 유리했습니다.

따라서 이 프로젝트의 결론은 다음과 같습니다.

> 모델은 위험 순서를 만들지만, 실제 리뷰 범위는 손실 규모, 개입 효과, 검토 비용, 고객 불편 비용 같은 비즈니스 가정이 결정한다.

---

## 2. Problem & Objective

신용 리스크 모델은 고객별 상환 불이행 위험 점수를 만들 수 있습니다. 하지만 실제 카드사 운영에서 점수 자체가 곧바로 의사결정이 되지는 않습니다.

리스크팀이 봐야 하는 것은 단순히 “누가 위험한가?”가 아니라, 제한된 검토 인력 안에서 **이번 달 누구를 먼저 볼 것인가**입니다.

이 판단에는 두 가지 비용이 함께 존재합니다.

| 판단 오류 | 발생하는 문제 |
|---|---|
| 너무 좁게 검토 | 실제 위험 고객을 놓쳐 신용손실이 커질 수 있음 |
| 너무 넓게 검토 | 정상 고객까지 검토해 운영 부담과 고객 경험 문제가 생김 |

따라서 리스크팀은 위험 점수뿐 아니라 검토 대상 규모, 위험 고객 포착 범위, 정상 고객 검토 부담을 함께 봐야 합니다.

본 프로젝트에서는 AMEX 데이터를 단순 default prediction 문제로만 다루지 않았습니다. 고객별 위험 점수를 만든 뒤, 이를 위험 구간, 리뷰 우선순위, 월별 검토 대상 목록, 비용 민감도 시뮬레이션으로 변환하는 문제로 재정의했습니다.

분석 목표는 다음과 같습니다.

첫째, 고객-월 데이터를 고객 단위 risk profile로 변환합니다.

둘째, 여러 모델을 사용해 안정적인 위험 순위 점수를 생성합니다.

셋째, 위험 점수 상위 구간별 Precision, Capture Rate, Lift, 정상 고객 검토 부담을 계산합니다.

넷째, 표본 구조를 고려해 non-default 고객 검토 부담을 보정합니다.

다섯째, EAD, LGD, 개입 효과, 검토 비용, 고객 불편 비용 가정에 따라 적절한 리뷰 범위가 어떻게 달라지는지 시뮬레이션합니다.

여섯째, 최종 점수를 월별 review queue와 monitoring workflow로 연결합니다.

---

## 3. Data

원본 데이터는 고객별 여러 달의 기록으로 구성되어 있습니다. 예측 대상은 고객 단위의 상환 불이행 여부이므로, 고객-월 데이터를 그대로 사용하는 것이 아니라 고객 한 명의 과거 행동을 요약한 customer-level risk profile로 변환했습니다.

변수명은 익명화되어 있어 개별 변수의 금융적 의미를 직접 해석하기 어렵습니다. 특정 변수를 소득, 한도, 연체처럼 단정하기보다, 고객의 장기 수준, 변동성, 최근 변화, 결측 패턴이 더 안정적인 리스크 신호가 될 수 있다고 보았습니다.

Feature block은 다음처럼 구성했습니다.

| Feature block | 보는 관점 | 리스크 해석 |
|---|---|---|
| Summary | 고객의 전반적 수준 | 장기적인 행동 수준 |
| Temporal | 처음과 마지막의 변화 | 시간에 따른 악화 또는 개선 |
| Recent window | 최근 3개월·6개월 패턴 | 최근 위험 신호 반영 |
| Missingness | 결측 개수와 비율 | 관측 가능성 또는 데이터 공백의 변화 |
| Pivot-lite | 월별 위치 정보 일부 보존 | 집계 과정에서 시간 순서 정보 손실 완화 |

최종 점수는 절대 확률이라기보다 위험 순위 점수로 해석했습니다.

그 이유는 공개 데이터의 표본 구조가 실제 카드 포트폴리오의 분포와 다를 수 있고, AMEX 데이터에서 non-default 표본은 실제 모집단 비율과 다르게 구성되어 있기 때문입니다. 따라서 본 프로젝트는 “확률 보정된 실제 부도율”보다 “리스크팀이 먼저 볼 고객을 잘 정렬하는가”에 초점을 두었습니다.

---

## 4. Method / System Design

이 프로젝트의 핵심은 단일 모델 성능이 아니라, 모델 점수를 운영 의사결정으로 변환하는 구조입니다.

전체 흐름은 다음과 같습니다.

```text
Raw Customer-Month Data
        ↓
Customer-level Risk Profile
(summary / temporal / recent / missingness / pivot-lite)
        ↓
Default Risk Score
(LightGBM / XGBoost / CatBoost / Tabular MLP / OOF blending)
        ↓
Risk Ranking
(customer-level review priority)
        ↓
Top-K Policy Simulation
(precision / capture / lift / non-default workload)
        ↓
Cost Scenario Analysis
(EAD / LGD / intervention effect / review cost / customer friction)
        ↓
Monthly Review Queue
        ↓
Monitoring & Validation
(shadow mode / drift / calibration / challenger model)
```

모델링은 다음 관점으로 구성했습니다.

| 구분 | 사용한 모델/변수 관점 | 역할 |
|---|---|---|
| 기준 모델 | 전체 변수 기반 LightGBM | 대규모 표 형식 데이터에서 빠른 기준선 생성 |
| 보조 부스팅 모델 | XGBoost, CatBoost | 다른 부스팅 구현에서도 위험 순위가 유지되는지 확인 |
| 중요 변수 모델 | 중요도 상위 변수 기반 LightGBM 변형 | 전체 변수 사용 시 생길 수 있는 잡음 의존도 점검 |
| 최근 변화 모델 | 최근 구간·변화량 중심 변수 | 장기 평균에 묻힐 수 있는 최근 악화 신호 보완 |
| 월별 위치 모델 | 월별 위치 정보 보존 변수 | 고객-월 집계 과정에서 사라질 수 있는 시간 위치 정보 보존 |
| 비트리 모델 | Tabular MLP | 트리 모델과 다른 함수 형태의 보조 후보 |
| 최종 결합 | 8개 모델 OOF 예측값 동일 가중 평균 | 단일 모델 의존도를 줄인 최종 위험 순위 점수 |

기준 모델은 LightGBM으로 잡았습니다. 고객 수와 변수 개수가 많은 tabular data이고, 변수 의미가 익명화되어 있으며, 결측 패턴과 비선형 관계가 함께 작동할 가능성이 컸기 때문입니다.

다만 최종 위험 순위를 기준 모델 하나에만 의존하지 않기 위해, 다양한 모델과 서로 다른 변수 묶음을 함께 실험했습니다. 같은 데이터라도 모델의 학습 방식과 입력 변수 관점이 달라지면 위험 신호를 포착하는 방식과 오류 패턴이 조금씩 달라질 수 있기 때문입니다.

각 모델의 점수는 fold 밖에서 예측된 OOF 점수를 기준으로 비교했습니다. 이후 여러 모델의 OOF 점수를 결합해 최종 위험 순위 점수를 만들었습니다.

---

## 5. Implementation

이 프로젝트는 모델링 노트북 하나로 끝나는 구조가 아니라, risk score를 운영 가능한 decisioning layer로 변환하는 구조를 목표로 했습니다.

구현 흐름은 다음과 같습니다.

1. 고객-월 데이터를 고객 단위 risk profile로 변환합니다.
2. Summary, Temporal, Recent window, Missingness, Pivot-lite feature를 생성합니다.
3. LightGBM, XGBoost, CatBoost, Tabular MLP 등 여러 모델을 학습합니다.
4. Fold 밖 OOF 예측값을 저장합니다.
5. 8개 모델 OOF 점수를 동일 가중 평균해 최종 위험 순위 점수를 만듭니다.
6. 고객을 위험 점수 순서대로 정렬합니다.
7. Top 1%, 5%, 10%, 20% 리뷰 구간별 trade-off를 계산합니다.
8. AMEX non-default sampling 구조를 고려해 정상 고객 검토 부담을 보정합니다.
9. EAD, LGD, 개입 효과, 검토 비용, 고객 불편 비용을 가정해 threshold 민감도 분석을 수행합니다.
10. 월별 review queue와 monitoring summary를 생성합니다.
11. decision mart와 dashboard prototype으로 결과를 조회할 수 있게 구성합니다.

운영 관점의 핵심 산출물은 다음과 같습니다.

| 산출물 | 역할 |
|---|---|
| Customer-level risk score | 고객별 리뷰 우선순위 점수 |
| Risk band | Critical / High / Watchlist / Standard 등 위험 구간 |
| Top-K policy table | 리뷰 범위별 Precision, Capture, Lift, workload 비교 |
| Population-adjusted workload | 표본 구조를 보정한 정상 고객 검토 부담 |
| Cost scenario table | 비용 가정별 최적 리뷰 범위 |
| Monthly review queue | 실제 리스크팀이 검토할 고객 목록 형태 |
| Monitoring summary | 월별 점수 분포, drift, capture, calibration 점검 |

이 구조의 목적은 좋은 모델 하나를 만드는 것이 아니라, **모델 점수를 리스크팀이 사용할 수 있는 리뷰 우선순위와 threshold 정책으로 번역하는 것**입니다.

---

## 6. Evaluation

평가는 단순 모델 성능표가 아니라, 위험 점수 상위 고객군에 실제 상환 불이행 고객이 얼마나 집중되는지를 기준으로 정리했습니다.

핵심 평가는 네 가지입니다.

1. 위험 점수 상위 구간이 실제 default를 잘 포착하는가?
2. 검토 범위를 넓히면 Capture Rate와 정상 고객 검토 부담이 어떻게 변하는가?
3. 점수 분위별 default rate가 단조적으로 정렬되는가?
4. 비용 가정에 따라 적절한 리뷰 threshold가 어떻게 달라지는가?

---

### 6.1 Top-K Review Policy Simulation

OOF 검증 점수로 고객을 위험도 순서대로 정렬했을 때, 상위 구간에는 관측된 불이행 고객이 강하게 집중되었습니다.

| 리뷰 구간 | 검토 대상 수 | 포착된 불이행 고객 | Capture Rate | Lift | 정상 고객 검토 부담 | 보정 후 정상 고객 검토 부담 | Precision | 보정 후 Precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Top 1% | 4,590 | 4,589 | 3.86% | 3.86 | 1 | 20 | 99.98% | 99.57% |
| Top 5% | 22,946 | 22,742 | 19.14% | 3.83 | 204 | 4,080 | 99.11% | 84.79% |
| Top 10% | 45,892 | 44,326 | 37.30% | 3.73 | 1,566 | 31,320 | 96.59% | 58.60% |
| Top 20% | 91,783 | 81,176 | 68.31% | 3.42 | 10,607 | 212,140 | 88.44% | 27.68% |

위험 점수 상위 구간에는 관측된 상환 불이행 고객이 강하게 집중되었습니다.

Top 5% 구간의 Precision은 99.11%, Lift는 3.83으로 높았지만, 전체 불이행 고객 중 포착 비율은 19.14%였습니다. 따라서 Top 5%는 전체 위험 고객을 충분히 포착하는 정책이라기보다, 우선 검토할 고위험 후보군으로 보는 것이 적절합니다.

검토 범위를 Top 20%까지 넓히면 Capture Rate는 68.31%까지 올라가지만, 정상 고객 검토 부담도 함께 증가합니다. 특히 AMEX 데이터의 표본 구조를 고려해 정상 고객을 20배로 보정하면, Top 20%의 보정 후 정상 고객 부담은 212,140명으로 커지고 보정 후 Precision은 27.68%까지 낮아집니다.

즉, 리뷰 구간은 Precision만이 아니라 포착률과 검토 부담의 균형으로 판단해야 합니다.

---

### 6.2 Score Band Analysis

고객을 위험 점수 기준 10개 분위로 나누어 확인했습니다.

가장 위험한 D1 구간의 관측 불이행률은 96.59%였고, 가장 낮은 D10 구간은 0.04%였습니다.

| 점수 분위 | 해석 |
|---|---|
| D1 | 가장 높은 위험 구간. 관측 불이행률 96.59% |
| D10 | 가장 낮은 위험 구간. 관측 불이행률 0.04% |

이 결과는 최종 점수가 일부 상위 고객만 선별한 것이 아니라, 전체 고객을 위험도 순서로 구분하는 데에도 일관되게 작동했음을 보여줍니다.

다만 이 값도 공개 데이터의 표본 구조를 반영한 관측 default rate이므로, 실제 카드 포트폴리오의 절대 부도율로 해석하면 안 됩니다.

중요한 해석은 다음입니다.

> 최종 위험 점수는 고객을 상대적 위험 순서로 정렬하는 데 유용했다.  
> 하지만 실제 운영에서는 이 점수를 확률이 아니라 리뷰 우선순위로 사용하는 것이 더 안전하다.

---

### 6.3 Threshold Sensitivity Analysis

앞선 결과는 위험 점수가 고객을 위험도 순서로 잘 정렬한다는 것을 보여줍니다. 하지만 실제 운영에서 중요한 질문은 “상위 몇 %까지 검토할 것인가?”입니다.

이 리뷰 범위는 모델 성능만으로 정해지지 않고, 손실 규모, 개입 효과, 검토 비용, 정상 고객 검토 부담에 따라 달라집니다.

기준 시나리오는 다음과 같이 설정했습니다.

| 항목 | 기준값 | 의미 |
|---|---:|---|
| EAD | 1.00 | 노출금액을 정규화 |
| LGD | 0.50 | 불이행 발생 시 손실률 |
| 개입 효과 | 0.20 | 리뷰/개입이 손실을 줄이는 비율 |
| 건당 검토 비용 | 0.010 | 고객 1명 검토 비용 |
| 고객 불편 비용 | 0.005 | 정상 고객 검토에 따른 friction cost |
| 정상 고객 보정 | 20배 | AMEX non-default sampling 구조 보정 |

정규화 순효익은 다음 방식으로 계산했습니다.

```text
예상 손실 절감액 = 포착된 불이행 고객 수 × EAD × LGD × 개입 효과

검토 비용 = 실질 검토량 × 건당 검토 비용

고객 불편 비용 = 보정 후 정상 고객 검토 부담 × 건당 고객 불편 비용

정규화 순효익 = 예상 손실 절감액 - 검토 비용 - 고객 불편 비용
```

기준 시나리오 결과는 다음과 같습니다.

| 리뷰 구간 | 포착된 불이행 고객 | 보정 후 정상 고객 부담 | 정규화 순효익 |
|---|---:|---:|---:|
| Top 5% | 22,742 | 4,080 | 1,985.58 |
| Top 10% | 44,326 | 31,320 | 3,519.54 |
| Top 17% | 71,205 | 136,220 | 4,365.15 |
| Top 20% | 81,176 | 212,140 | 4,123.74 |

기준 시나리오에서는 Top 17%가 가장 높은 순효익을 보였습니다.

Top 20%는 더 많은 불이행 고객을 포착하지만, 보정 후 정상 고객 검토 부담이 212,140명까지 커지면서 순효익은 오히려 낮아졌습니다.

즉, Capture Rate를 높이는 정책이 항상 더 좋은 운영 정책은 아닙니다.

---

### 6.4 Cost Scenario별 최적 리뷰 범위

비용 가정을 바꾸면 적절한 리뷰 범위도 달라졌습니다.

| 시나리오 | 해석 | 가장 높은 순효익 구간 |
|---|---|---|
| Conservative | 검토 비용과 고객 불편 비용을 더 크게 보는 가정 | Top 4% |
| Base | 기준 가정 | Top 17% |
| Aggressive | 손실 규모와 개입 효과를 더 크게 보는 가정 | Top 28% |

이 분석의 핵심은 특정 구간을 정답으로 제시하는 것이 아닙니다.

모델은 위험 순서를 만들지만, 리뷰 범위는 비즈니스 가정이 결정합니다. 실제 운영 전에는 고객별 EAD, 실제 LGD, 회수율, 개입 효과, 검토 비용, 고객 경험 비용을 추가로 측정해야 합니다.

즉, 위험 점수는 누구를 먼저 볼지 알려주지만, 어디까지 볼지는 모델이 아니라 비즈니스 비용 구조가 결정합니다.

---

### 6.5 운영 해석

전체 결과를 운영 관점으로 요약하면 다음과 같습니다.

| 질문 | 결과 | 운영 해석 |
|---|---|---|
| 위험 점수 상위 구간에 default가 집중되는가? | Top 10%가 전체 default의 37.30% 포착 | 리뷰 우선순위 점수로 사용 가능 |
| 상위 구간 Precision은 높은가? | 관측 기준 Top 10% Precision 96.59% | 표본 내 위험 집중도는 높음 |
| 보정 후 정상 고객 부담은 어떤가? | Top 20% 보정 후 정상 고객 부담 212,140명 | 넓은 리뷰 정책은 운영 부담 큼 |
| 가장 좋은 threshold는 고정되어 있는가? | 비용 시나리오별 Top 4%~28%로 변화 | threshold는 비즈니스 비용 구조에 따라 결정 |
| 점수를 자동 조치에 써도 되는가? | 공개 데이터·익명 변수·EAD/LGD 부재 | 자동 조치보다 review prioritization 용도가 적절 |

따라서 최종 결과는 다음처럼 해석하는 것이 안전합니다.

> 이 모델은 고객을 위험 순서로 정렬하는 데 유용하다.  
> 하지만 실제 카드사 운영에서는 자동 조치 시스템이 아니라, 리스크팀의 월별 리뷰 우선순위와 threshold 시뮬레이션 도구로 사용하는 것이 적절하다.

---

## 7. Key Design Decisions

### 왜 default prediction이 아니라 review prioritization으로 정의했는가?

카드사는 모든 고객을 매월 자세히 검토할 수 없습니다. 따라서 중요한 질문은 “누가 default할까?”가 아니라 “이번 달 누구를 먼저 볼 것인가?”입니다.

이 프로젝트는 예측 점수를 실제 운영에서 사용할 수 있도록 Top-K review policy와 threshold simulation으로 변환했습니다.

### 왜 고객-월 데이터를 customer-level profile로 변환했는가?

원본 데이터는 여러 달의 고객 기록으로 구성되어 있지만, 예측 대상은 고객 단위 default 여부입니다.

따라서 고객-월 데이터를 그대로 사용하기보다, 고객별 장기 수준, 최근 변화, 변동성, 결측 패턴을 요약한 customer-level profile로 변환했습니다.

### 왜 변수 의미를 직접 해석하지 않았는가?

AMEX 데이터는 변수명이 익명화되어 있습니다. 특정 변수를 소득, 한도, 연체처럼 단정하면 잘못된 금융적 해석이 될 수 있습니다.

그래서 변수의 이름보다 시간적 패턴, 결측 패턴, 최근 변화, 모델 간 반복적으로 나타나는 위험 신호를 중심으로 해석했습니다.

### 왜 여러 모델을 결합했는가?

단일 모델은 특정 feature나 특정 학습 방식에 과도하게 의존할 수 있습니다.

LightGBM, XGBoost, CatBoost, Tabular MLP, feature subset 모델을 함께 사용하고 OOF 기반으로 결합해, 여러 모델이 공통적으로 높게 본 위험 신호를 최종 점수에 반영했습니다.

### 왜 Top-K 기준으로 평가했는가?

실제 리스크팀은 모든 고객을 볼 수 없고, 위험 상위 구간부터 검토합니다.

따라서 전체 AUC나 Accuracy보다 Top 1%, 5%, 10%, 20% 구간에서의 Precision, Capture Rate, Lift, 정상 고객 검토 부담이 더 운영적인 평가 기준입니다.

### 왜 non-default workload를 보정했는가?

AMEX 공개 데이터는 실제 카드 포트폴리오의 default/non-default 비율을 그대로 반영하지 않을 수 있습니다.

따라서 정상 고객 검토 부담을 보정해, 실제 운영에서 리뷰 범위를 넓힐 때 발생할 수 있는 workload를 더 보수적으로 확인했습니다.

### 왜 비용 민감도 분석을 추가했는가?

위험 점수는 고객 순서를 만들지만, 리뷰 범위는 비즈니스 비용 구조가 결정합니다.

EAD, LGD, 개입 효과, 검토 비용, 고객 불편 비용에 따라 적절한 threshold는 달라집니다. 그래서 Base, Conservative, Aggressive 시나리오를 나누어 리뷰 범위가 어떻게 변하는지 확인했습니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 default prediction 모델링 문제처럼 보였습니다.

하지만 분석을 진행하면서 핵심은 “가장 높은 성능의 모델 하나를 만드는 것”이 아니라, **그 모델 점수를 리스크팀이 쓸 수 있는 의사결정 구조로 바꾸는 것**이라는 점이 분명해졌습니다.

첫 번째 전환점은 feature 설계였습니다. 변수명이 익명화되어 있기 때문에 개별 변수의 의미를 금융적으로 단정하는 대신, summary, temporal, recent, missingness, pivot-lite feature block으로 고객 행동 패턴을 요약했습니다.

두 번째 전환점은 평가 기준이었습니다. 단순 AUC나 Accuracy보다 리스크팀이 실제로 사용할 Top-K review policy가 더 중요했습니다. 그래서 위험 점수 상위 1%, 5%, 10%, 20%에서 default concentration, capture rate, lift, false positive load를 비교했습니다.

세 번째 전환점은 non-default sampling 보정이었습니다. 관측 precision만 보면 상위 구간이 매우 좋아 보이지만, 실제 운영에서는 정상 고객 수가 훨씬 많을 수 있습니다. 그래서 정상 고객 검토 부담을 보정해 threshold를 더 보수적으로 해석했습니다.

네 번째 전환점은 cost scenario였습니다. Top 20%는 더 많은 default를 포착하지만, 정상 고객 검토 부담이 커져 기준 시나리오에서는 Top 17%보다 순효익이 낮았습니다. 이 결과를 통해 “많이 잡는 정책”이 항상 좋은 정책은 아니라는 점을 확인했습니다.

최종적으로 이 프로젝트는 다음 메시지로 정리되었습니다.

> 좋은 default model은 확률을 맞히는 데서 끝나지 않는다.  
> 카드회사에서는 그 점수를 제한된 review capacity 안에서 누구를 먼저 검토할지 결정하는 risk decisioning 구조로 바꿀 수 있어야 한다.

---

## 9. Limitations

이 프로젝트는 American Express 공개 데이터를 활용한 포트폴리오 프로토타입이므로, 실제 카드사 운영 정책으로 바로 해석하기에는 한계가 있습니다.

첫째, 공개 데이터의 표본 분포는 실제 카드 포트폴리오의 분포와 다를 수 있습니다. 따라서 관측 precision이나 default rate를 실제 모집단 확률로 직접 해석하면 안 됩니다.

둘째, 변수명이 익명화되어 있어 개별 변수의 금융적 의미를 직접 해석하기 어렵습니다. feature importance를 금융 정책 근거로 바로 사용하는 것은 적절하지 않습니다.

셋째, 고객별 EAD, 실제 LGD, 회수율, 개입 효과, 검토 비용 정보가 포함되어 있지 않습니다. 따라서 threshold 분석은 실제 손익 추정이 아니라, 가정에 기반해 리뷰 범위가 어떻게 달라질 수 있는지 확인하기 위한 민감도 분석입니다.

넷째, 모델 개입의 인과효과를 검증하지 않았습니다. 위험 고객을 검토했을 때 실제 default가 얼마나 줄어드는지는 별도 실험이나 shadow mode 운영으로 확인해야 합니다.

다섯째, 실제 카드사 운영에는 규제, 설명 가능성, 공정성, 고객 고지, adverse action 관련 검토가 필요합니다. 이 프로젝트는 자동 조치 시스템이 아니라 review prioritization prototype으로 해석해야 합니다.

---

## 10. How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Build features and model scores

```bash
PYTHONPATH=$PWD:$PYTHONPATH python scripts/00_build_customer_profile.py
PYTHONPATH=$PWD:$PYTHONPATH python scripts/01_train_base_models.py
PYTHONPATH=$PWD:$PYTHONPATH python scripts/02_blend_oof_scores.py
```

### Run decisioning analysis

```bash
PYTHONPATH=$PWD:$PYTHONPATH python scripts/03_topk_policy_simulation.py
PYTHONPATH=$PWD:$PYTHONPATH python scripts/04_cost_scenario_analysis.py
PYTHONPATH=$PWD:$PYTHONPATH python scripts/05_build_monthly_review_queue.py
PYTHONPATH=$PWD:$PYTHONPATH python scripts/build_decision_mart.py
```

### Launch dashboard

```bash
streamlit run app.py
```

실행 결과는 `outputs/` 또는 decision mart database에 저장됩니다.

---

## 11. Project Structure

```text
amex-credit-risk-decisioning/
├── README.md
├── requirements.txt
├── app.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── decision_mart/
├── notebooks/
│   ├── 01_feature_engineering.ipynb
│   ├── 02_model_training.ipynb
│   ├── 03_topk_policy_simulation.ipynb
│   ├── 04_cost_scenario_analysis.ipynb
│   └── 05_dashboard_review.ipynb
├── scripts/
│   ├── 00_build_customer_profile.py
│   ├── 01_train_base_models.py
│   ├── 02_blend_oof_scores.py
│   ├── 03_topk_policy_simulation.py
│   ├── 04_cost_scenario_analysis.py
│   ├── 05_build_monthly_review_queue.py
│   └── build_decision_mart.py
├── src/
│   └── amex_risk/
│       ├── features.py
│       ├── models.py
│       ├── ranking.py
│       ├── simulation.py
│       ├── decision_mart.py
│       └── monitoring.py
└── outputs/
    ├── tables/
    └── figures/
```

---

## 12. What This Project Demonstrates

이 프로젝트는 신용카드 상환 불이행 예측 점수를 실제 리스크 운영 의사결정으로 바꾸는 과정을 보여줍니다.

첫째, 고객-월 익명 데이터를 customer-level risk profile로 변환하고, summary, temporal, recent, missingness, pivot-lite feature block을 설계했습니다.

둘째, LightGBM, XGBoost, CatBoost, Tabular MLP 등 여러 모델을 사용해 단일 모델 의존도를 줄였습니다.

셋째, OOF 기반 blending으로 최종 위험 순위 점수를 만들었습니다.

넷째, 모델 점수를 절대 확률이 아니라 제한된 리뷰 자원 안에서 사용할 ranking-oriented score로 해석했습니다.

다섯째, Top-K policy simulation으로 리뷰 구간별 Precision, Capture Rate, Lift, 정상 고객 검토 부담을 비교했습니다.

여섯째, AMEX 데이터의 표본 구조를 고려해 non-default workload를 보정했습니다.

일곱째, EAD, LGD, 개입 효과, 검토 비용, 고객 불편 비용을 가정한 cost-sensitive threshold analysis를 수행했습니다.

여덟째, 위험 점수를 monthly review queue, decision mart, dashboard, monitoring workflow로 연결했습니다.

이 프로젝트의 핵심은 단순히 default prediction 모델을 만든 것이 아니라, **모델 점수를 카드사 리스크팀이 사용할 수 있는 리뷰 우선순위와 threshold 의사결정 구조로 변환한 것**입니다.
