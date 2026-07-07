# Dominick's Price Elasticity IV-DML

Dominick's retail scanner 데이터를 활용해 가격 변화가 상품 판매량에 미치는 영향을 추정한 가격탄력성 분석 프로젝트입니다.

이 프로젝트는 가격과 판매량의 단순 상관관계를 보는 것이 아니라, **가격 내생성**을 고려하기 위해 비용 변동을 도구변수로 사용하고, FE-IV, Dynamic FE-IV, FD-PLIV-DML 결과를 비교합니다.

---

## 1. Overview

소매 데이터에서 가격과 판매량의 관계를 해석하는 것은 생각보다 어렵습니다. 가격이 오르면 판매량이 줄어드는지 알고 싶지만, 실제 데이터에서는 가격이 무작위로 변하지 않습니다.

예를 들어 수요가 높을 것으로 예상되는 시기에는 가격이 달라질 수 있고, 프로모션이나 진열, 재고, 경쟁 상품 가격, 매장 특성도 가격과 판매량에 동시에 영향을 줄 수 있습니다. 그래서 단순히 가격과 판매량을 회귀분석하면 “가격 때문에 판매량이 변한 것인지”, 아니면 “수요 상황이 가격과 판매량을 동시에 움직인 것인지” 구분하기 어렵습니다.

이 프로젝트는 Dominick's retail scanner 데이터의 결과 테이블을 바탕으로, cereal, canned soup, bottled juices, cookies 네 개 카테고리에서 자기 상품 가격 변화가 자기 상품 판매량에 미치는 영향을 추정합니다.

핵심 접근은 **FE-IV**입니다. 상품-매장 조합의 고정 특성과 주차별 공통 충격을 통제한 뒤, 가격을 비용으로 도구화하여 가격 변화의 외생적 부분을 활용합니다.

추가로 Dynamic FE-IV를 사용해 가격 효과가 현재 시점에만 나타나는지, 시차를 두고 누적되는지 확인했습니다. 마지막으로 FD-PLIV-DML을 통해 first difference와 machine learning 기반 nuisance model을 사용한 partial IV 결과를 비교했습니다.

주요 결론은 다음과 같습니다.

대부분의 기본 FE-IV 결과와 DML 결과에서 가격 상승은 자기 상품 판매량 감소와 같은 방향을 보였습니다. 다만 계수 크기는 카테고리, 통제 변수, deal 변수 포함 여부, lag 구조, 추정 방법에 따라 크게 달라졌습니다.

따라서 이 프로젝트의 결론은 “하나의 정확한 가격탄력성 숫자”를 제시하는 것이 아니라, **가격 효과의 방향성은 비교적 일관되지만 절대 크기는 식별 전략과 사양에 민감하다**는 것입니다.

---

## 2. Problem & Objective

이 프로젝트의 핵심 질문은 다음과 같습니다.

> 비용 기반 가격 변동을 이용하면, 상품-매장 고정 특성과 주차별 공통 충격을 통제한 뒤에도 소매 상품의 가격탄력성을 추정할 수 있는가?

소매 가격탄력성은 마케팅, 가격 정책, 수요 예측, 프로모션 전략에서 중요한 지표입니다. 하지만 실제 retail scanner 데이터에서는 가격이 단순히 외부에서 주어진 변수가 아닙니다.

가격은 다음 요인들과 함께 움직일 수 있습니다.

- 특정 상품의 예상 수요
- 매장별 고객 규모와 방문 패턴
- 프로모션과 할인 행사
- 경쟁 상품 가격
- 제조사 또는 브랜드 전략
- 재고와 공급 비용
- 계절성 또는 주차별 공통 수요 충격

이 때문에 단순 OLS로 가격과 판매량을 연결하면 가격 효과가 왜곡될 수 있습니다.

이 프로젝트의 목표는 세 가지입니다.

첫째, 가격 내생성을 고려하기 위해 비용 변동을 도구변수로 사용하는 FE-IV 분석을 수행합니다.

둘째, 가격 효과가 현재 가격에만 나타나는지, lagged price까지 포함했을 때 누적 효과가 어떻게 바뀌는지 확인합니다.

셋째, 전통적인 FE-IV 결과와 FD-PLIV-DML 결과를 비교해 가격 효과 추정이 모델 선택과 통제 방식에 얼마나 민감한지 검토합니다.

이 프로젝트는 “가격탄력성 하나를 계산했다”보다, **가격탄력성을 추정할 때 어떤 식별 문제와 robustness 문제가 생기는지 보여주는 것**에 초점을 둡니다.

---

## 3. Data

이 프로젝트는 Dominick's retail scanner 데이터를 기반으로 합니다.

원자료는 대용량 store-upc-week 패널 구조입니다. 즉, 특정 매장의 특정 상품이 특정 주에 어떤 가격과 판매량을 보였는지를 관측하는 구조입니다.

다만 GitHub 저장소에는 원본 패널 파일을 포함하지 않았습니다. 원자료 크기가 크기 때문에, 이 포트폴리오 저장소에는 분석 결과를 재현하고 해석할 수 있도록 가공된 결과 CSV와 figure만 포함했습니다.

분석 대상 카테고리는 다음 네 개입니다.

- cereal
- canned soup
- bottled juices
- cookies

각 카테고리는 수백만 건 이상의 store-upc-week 관측치를 포함합니다. 기본 FE-IV 결과 기준으로 대략 다음 규모의 분석이 사용되었습니다.

| 카테고리 | 기본 분석 관측치 규모 | 상품-매장 클러스터 수 | 주차 수 |
|---|---:|---:|---:|
| cereal | 약 645만 건 | 약 36,438개 | 366주 |
| canned soup | 약 686만 건 | 약 32,693개 | 378주 |
| bottled juices | 약 611만 건 | 약 36,386개 | 392주 |
| cookies | 약 1,315만 건 | 약 78,134개 | 388주 |

주요 변수는 다음과 같이 이해할 수 있습니다.

- 판매량: 특정 상품의 주별 판매량
- 가격: 특정 상품의 주별 판매 가격
- 비용: 가격을 도구화하기 위한 비용 변수
- 고객 수 관련 변수: 매장 또는 카테고리별 수요 환경을 통제하기 위한 변수
- deal 여부: 프로모션 또는 할인 행사 여부
- 경쟁 상품 관련 변수: 같은 카테고리 안에서 다른 상품의 비용·가격·프로모션 상황
- 상품-매장 식별자: 같은 상품이 같은 매장에서 반복 관측되는 패널 구조
- 주차 정보: 특정 주의 공통 수요 충격을 통제하기 위한 시간 단위

원자료를 직접 포함하지 않은 대신, `outputs/tables/model_results/` 아래에 다음 결과표를 포함했습니다.

- FE-IV baseline results
- FE-IV sales decomposition results
- first-stage strength results
- dynamic distributed-lag IV results
- FD-PLIV-DML validation results
- robustness summaries

따라서 이 저장소의 목적은 원자료를 처음부터 다시 처리하는 것이 아니라, **대용량 원패널에서 생성된 결과 테이블을 바탕으로 분석 결론과 시각화를 재현하는 것**입니다.

---

## 4. Method / System Design

이 프로젝트의 핵심 방법론은 **FE-IV**입니다.

기본 아이디어는 가격을 직접 설명 변수로 넣는 것이 아니라, 비용 변동을 도구변수로 사용해 가격 변화 중 상대적으로 외생적인 부분을 활용하는 것입니다.

기본 구조는 다음과 같습니다.

첫째, 가격은 판매량에 영향을 미치는 핵심 설명 변수입니다.

둘째, 가격은 수요 충격이나 프로모션과 함께 움직일 수 있으므로 내생적일 수 있습니다.

셋째, 비용은 가격을 움직이는 중요한 요인이지만, 적절한 통제와 Fixed Effects 이후에는 수요 충격과 직접적으로 연결되지 않는다는 가정 아래 도구변수로 사용합니다.

넷째, 상품-매장 Fixed Effects와 week Fixed Effects를 포함해 고정적인 상품-매장 차이와 주차별 공통 충격을 통제합니다.

기본 FE-IV 분석 외에도 다음 분석을 수행했습니다.

### Dynamic FE-IV

현재 가격만 포함하는 모형은 가격 효과가 같은 주에 모두 반영된다고 가정합니다. 하지만 소비자는 가격 변화에 즉시 반응할 수도 있고, 재고 구매나 지연 반응 때문에 효과가 여러 주에 걸쳐 나타날 수도 있습니다.

그래서 현재 가격과 lagged price를 함께 넣은 distributed lag 구조를 사용했습니다. 이를 통해 현재 효과와 누적 효과가 어떻게 달라지는지 확인했습니다.

### Sales decomposition

가격 변화가 자기 상품 판매량에만 영향을 주는지, 같은 제조사 상품, 경쟁 제조사 상품, 카테고리 전체 판매량에는 어떤 패턴이 나타나는지도 확인했습니다.

이 분석은 가격탄력성을 단일 상품의 수요 반응으로만 보지 않고, 카테고리 내부의 대체 관계와 함께 해석하기 위한 것입니다.

### FD-PLIV-DML

FE-IV 결과가 선형 통제 방식에 의존할 수 있기 때문에, first difference와 partial IV 구조를 결합한 FD-PLIV-DML 결과도 확인했습니다.

DML에서는 Ridge와 LightGBM을 nuisance model로 사용해, 가격·비용·판매량의 예측 가능한 부분을 제거한 뒤 남은 변동으로 가격 효과를 추정했습니다.

이 방법은 FE-IV와 완전히 같은 수치를 목표로 하기보다는, 다른 추정 전략에서도 가격 효과의 방향이 유지되는지 확인하는 validation 역할을 합니다.

---

## 5. Implementation

이 프로젝트는 원패널 전체를 GitHub에서 다시 적재하지 않고, 결과 CSV와 notebook을 중심으로 구성했습니다.

전체 구현 흐름은 다음과 같습니다.

1. 대용량 Dominick's 원패널에서 카테고리별 FE-IV, Dynamic FE-IV, FD-PLIV-DML 결과를 생성합니다.
2. GitHub 저장소에는 원패널 대신 결과 CSV를 보관합니다.
3. Notebook은 결과 CSV를 읽어 핵심 표와 그림을 재생성합니다.
4. 각 notebook은 분석 단계별로 역할을 나누어 결과를 해석합니다.

현재 저장소의 notebook 구성은 다음과 같습니다.

- `01_results_overview.ipynb`  
  포함된 결과 CSV의 구조와 카테고리별 분석 범위를 확인합니다.

- `02_fe_iv_baseline_results.ipynb`  
  FE-IV 기준 결과, own-price elasticity, first-stage strength, sales decomposition을 정리합니다.

- `03_dynamic_iv_robustness.ipynb`  
  현재 가격만 사용한 결과와 lagged price를 포함한 distributed lag 결과를 비교합니다.

- `04_dml_validation_interpretation.ipynb`  
  FD-PLIV-DML 결과를 FE-IV 결과와 비교하고, 가격 효과 추정이 방법론에 얼마나 민감한지 해석합니다.

결과 파일은 `outputs/tables/model_results/` 아래에 카테고리별로 저장되어 있습니다. 그림은 `outputs/figures/` 아래에 저장되어 있습니다.

이 구조를 선택한 이유는 포트폴리오 저장소의 목적 때문입니다. 이 프로젝트의 핵심은 원자료 처리 전체를 GitHub에 올리는 것이 아니라, 대용량 분석에서 생성된 결과를 바탕으로 **가격탄력성 추정의 방향성, 민감도, robustness를 재현 가능하게 보여주는 것**입니다.

---

## 6. Evaluation

이 프로젝트의 평가는 단일 가격탄력성 숫자 하나를 고르는 방식으로 하지 않았습니다.

대신 다음 네 가지를 함께 확인했습니다.

1. FE-IV에서 가격 계수가 음의 방향을 보이는가?
2. 비용 도구변수가 가격을 충분히 설명하는가?
3. deal 변수와 rival 변수 등 통제 방식에 따라 계수가 얼마나 움직이는가?
4. Dynamic FE-IV와 FD-PLIV-DML에서도 가격 효과의 방향이 유지되는가?

### FE-IV own-sales 결과

기본 FE-IV 결과에서 대부분의 카테고리는 가격 상승과 자기 상품 판매량 감소의 관계를 보였습니다.

| 카테고리 | 기본 FE-IV 계수 | 고객 수 통제 후 | deal 포함 후 | full sensitivity |
|---|---:|---:|---:|---:|
| cereal | -1.222 | -1.156 | -0.154 | -1.375 |
| canned soup | -0.224 | -0.285 | +0.391 | -1.036 |
| bottled juices | -0.213 | -0.189 | +0.410 | -1.074 |
| cookies | -1.498 | -1.716 | -0.597 | -1.094 |

이 표에서 가장 중요한 점은 단순히 계수가 음수라는 것이 아닙니다.

cereal과 cookies는 여러 사양에서 비교적 일관되게 음의 가격 효과를 보입니다. 반면 canned soup와 bottled juices는 deal 변수를 포함하면 계수 부호가 양수로 바뀌기도 합니다. 이는 가격 변화와 프로모션 변수가 강하게 얽혀 있음을 보여줍니다.

즉, 가격 효과는 존재하는 방향성이 있지만, **프로모션과 가격을 어떻게 분리하느냐에 따라 추정치가 크게 달라질 수 있습니다.**

### First-stage strength

도구변수 분석에서는 비용이 가격을 충분히 설명하는지 확인해야 합니다.

이 프로젝트의 first-stage t-stat은 모든 카테고리에서 일반적인 약한 도구변수 우려 기준을 크게 넘었습니다. 기본 FE-IV 결과 기준으로 first-stage t-stat은 대략 다음 범위였습니다.

- cereal: 약 58~65
- canned soup: 약 81~93
- bottled juices: 약 24~26
- cookies: 약 26~30

two-way clustering을 적용해도 주요 first-stage 강도는 상당히 높게 유지되었습니다.

따라서 이 프로젝트에서 더 중요한 문제는 “도구변수가 약한가?”보다는, **비용이 가격을 통해서만 판매량에 영향을 준다고 볼 수 있는가**, 즉 exclusion restriction 해석입니다.

### Dynamic FE-IV 결과

Dynamic FE-IV에서는 현재 가격만 넣은 모형과 lagged price를 함께 넣은 모형을 비교했습니다.

결과적으로 lag를 추가하면 일부 카테고리에서 누적 효과가 약해지거나 부호가 바뀌었습니다.

cereal은 고객 수 통제 기준으로 현재 가격만 보면 음의 효과가 뚜렷했지만, lag를 추가하면 누적 효과가 약해졌습니다. canned soup와 bottled juices는 lag 구조에 따라 누적 효과가 양의 방향으로 바뀌기도 했습니다. 반면 cookies는 lag를 추가해도 음의 누적 효과가 비교적 유지되었습니다.

이 결과는 단순 current-price 결과만으로 장기 가격 반응을 해석하면 위험하다는 점을 보여줍니다.

### FD-PLIV-DML 결과

FD-PLIV-DML 결과에서는 네 개 카테고리 모두 강한 음의 가격 효과가 나타났습니다.

| 카테고리 | DML 고객 수 통제 | DML deal 포함 |
|---|---:|---:|
| cereal | 약 -3.44 | 약 -2.85~-2.90 |
| canned soup | 약 -2.98 | 약 -2.23~-2.44 |
| bottled juices | 약 -3.42 | 약 -2.76~-2.92 |
| cookies | 약 -3.04 | 약 -2.18~-2.38 |

DML 결과는 FE-IV보다 훨씬 큰 음의 계수를 보였습니다. 따라서 두 방법은 “가격 상승이 판매량 감소와 연결된다”는 방향성에서는 일치하지만, 절대적인 탄력성 크기에서는 차이가 큽니다.

이 프로젝트의 최종 평가는 다음과 같습니다.

> 가격 상승과 자기 상품 판매량 감소의 방향성은 여러 분석에서 대체로 확인된다.  
> 그러나 가격탄력성의 절대 크기는 통제 변수, deal 처리, lag 구조, 추정 방법에 따라 크게 달라진다.  
> 따라서 단일 탄력성 숫자보다 식별 전략과 robustness를 함께 제시하는 것이 더 적절하다.

---

## 7. Key Design Decisions

### 왜 단순 OLS가 아니라 FE-IV를 사용했는가?

가격은 수요와 동시에 움직일 수 있습니다. 수요가 높을 것으로 예상되는 주에는 가격이 달라질 수 있고, 프로모션 기간에는 가격과 판매량이 동시에 변합니다.

따라서 단순 OLS는 가격 효과를 왜곡할 수 있습니다. 이 프로젝트는 비용 변동을 도구변수로 사용해 가격 변화 중 비용에서 비롯된 부분을 활용했습니다.

### 왜 상품-매장 Fixed Effects를 사용했는가?

같은 상품이라도 매장마다 평균 판매량이 다르고, 같은 매장이라도 상품별 고객층이 다를 수 있습니다.

상품-매장 Fixed Effects는 특정 상품이 특정 매장에서 원래 가지고 있는 평균적인 차이를 통제합니다. 이를 통해 “항상 잘 팔리는 상품”이나 “항상 많이 팔리는 매장”의 고정적인 차이가 가격 효과로 해석되는 것을 줄입니다.

### 왜 week Fixed Effects를 사용했는가?

소매 판매량은 특정 주의 공통 수요 충격에 영향을 받을 수 있습니다. 예를 들어 명절, 계절성, 거시적 소비 변화, 전체 프로모션 시즌은 여러 상품과 매장에 동시에 영향을 줄 수 있습니다.

week Fixed Effects는 이런 주차별 공통 충격을 통제하기 위한 것입니다.

### 왜 deal 변수를 따로 확인했는가?

소매 데이터에서 deal은 매우 중요합니다. 가격 인하는 단순 가격 변화가 아니라 프로모션, 진열, 광고, 할인 이벤트와 함께 발생할 수 있습니다.

FE-IV 결과에서 deal 변수를 포함하면 canned soup와 bottled juices의 계수 부호가 바뀌었습니다. 이는 가격 효과와 프로모션 효과가 강하게 얽혀 있다는 신호입니다.

그래서 이 프로젝트는 deal 변수를 단순 통제 변수로만 취급하지 않고, 결과 해석에서 중요한 민감도 요인으로 다루었습니다.

### 왜 Dynamic FE-IV를 추가했는가?

가격 효과가 반드시 같은 주에만 나타난다고 볼 수는 없습니다. 소비자는 가격이 낮을 때 미리 구매할 수 있고, 가격 변화의 영향이 다음 주 판매량으로 이어질 수도 있습니다.

Dynamic FE-IV는 현재 가격과 lagged price를 함께 넣어, 가격 효과의 누적 패턴을 확인하기 위한 분석입니다.

### 왜 FD-PLIV-DML을 추가했는가?

FE-IV는 선형 통제와 고정효과 구조에 의존합니다. 하지만 retail scanner 데이터는 매우 크고, 통제 변수와 수요 환경의 관계가 단순 선형이 아닐 수 있습니다.

FD-PLIV-DML은 first difference로 고정적인 수준 차이를 줄이고, Ridge와 LightGBM을 사용해 판매량·가격·비용의 예측 가능한 부분을 제거한 뒤 가격 효과를 추정합니다.

이 프로젝트에서 DML은 최종 정답이라기보다, FE-IV 결과의 방향성을 다른 방식으로 확인하는 validation 역할을 합니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 가격탄력성을 하나의 숫자로 추정하는 문제처럼 보일 수 있습니다.

하지만 분석을 진행하면서 핵심은 “정확한 탄력성 하나를 고르는 것”이 아니라, 가격 효과가 어떤 사양에서 안정적이고 어떤 사양에서 민감한지를 확인하는 것이라는 점이 분명해졌습니다.

첫 번째 전환점은 deal 변수였습니다. 기본 FE-IV에서는 대부분의 카테고리에서 음의 가격 효과가 나타났지만, deal 변수를 포함하면 일부 카테고리의 계수가 크게 이동하거나 부호가 바뀌었습니다. 이는 가격과 프로모션을 분리하지 않으면 가격탄력성 해석이 왜곡될 수 있음을 보여줍니다.

두 번째 전환점은 Dynamic FE-IV였습니다. 현재 가격만 보면 음의 효과가 뚜렷해 보이던 카테고리도 lag를 추가하면 누적 효과가 약해지거나 부호가 바뀌었습니다. 이는 단기 가격 반응과 누적 가격 반응이 다를 수 있다는 점을 보여줍니다.

세 번째 전환점은 DML 결과였습니다. DML은 네 개 카테고리 모두에서 강한 음의 효과를 보였지만, FE-IV보다 훨씬 큰 계수를 산출했습니다. 따라서 방향성은 일치하지만, 절대 크기는 방법론에 따라 민감하다는 결론을 내렸습니다.

결과적으로 이 프로젝트의 메시지는 다음처럼 정리되었습니다.

> 가격 상승은 판매량 감소와 대체로 연결된다.  
> 하지만 가격탄력성의 크기는 deal 처리, lag 구조, 통제 변수, 추정 방법에 민감하다.  
> 따라서 하나의 숫자보다 여러 식별 전략과 robustness 검증을 함께 제시해야 한다.

---

## 9. Limitations

이 프로젝트는 대용량 retail scanner 결과를 바탕으로 가격탄력성을 분석하지만, 몇 가지 한계가 있습니다.

첫째, 원본 패널 데이터를 GitHub에 포함하지 않았습니다. 저장소에는 가공된 결과 CSV와 figure만 포함되어 있으므로, 원자료 적재부터 전체 분석을 완전히 재실행하는 구조는 아닙니다.

둘째, 비용을 도구변수로 사용하는 FE-IV는 exclusion restriction에 의존합니다. 비용이 가격을 통해서만 판매량에 영향을 준다는 가정은 강한 가정이며, 완전히 검증하기 어렵습니다.

셋째, deal 변수와 가격은 강하게 얽혀 있습니다. 일부 카테고리에서는 deal 포함 여부에 따라 가격 계수가 크게 달라지거나 부호가 바뀌었습니다.

넷째, 카테고리별 결과 차이가 큽니다. cereal과 cookies는 비교적 음의 가격 효과가 안정적으로 나타났지만, canned soup와 bottled juices는 사양에 더 민감했습니다.

다섯째, Dynamic FE-IV 결과는 가격 효과의 시간 구조가 단순하지 않음을 보여줍니다. 현재 가격 효과만으로 장기 반응을 해석하기 어렵습니다.

여섯째, DML 결과는 FE-IV와 방향은 같지만 계수 크기가 훨씬 큽니다. 따라서 DML 결과를 그대로 최종 탄력성 숫자로 받아들이기보다는, 방법론 간 민감도 확인으로 해석하는 것이 안전합니다.

따라서 이 프로젝트의 결론은 다음처럼 제한적으로 해석해야 합니다.

> 가격 상승과 판매량 감소의 관계는 여러 방법에서 대체로 확인된다.  
> 그러나 절대적인 가격탄력성 크기는 사양과 추정 방법에 민감하므로, 단일 숫자로 결론 내리기보다 robustness와 식별 가정을 함께 제시해야 한다.

---

## 10. How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Execute notebooks

```bash
cd notebooks

python -m nbconvert --to notebook --execute 01_results_overview.ipynb --inplace
python -m nbconvert --to notebook --execute 02_fe_iv_baseline_results.ipynb --inplace
python -m nbconvert --to notebook --execute 03_dynamic_iv_robustness.ipynb --inplace
python -m nbconvert --to notebook --execute 04_dml_validation_interpretation.ipynb --inplace
```

Notebook은 `outputs/tables/model_results/`의 결과 CSV를 읽어 주요 표와 그림을 재생성합니다.

원본 Dominick's 패널 데이터는 저장소에 포함되어 있지 않으므로, 이 저장소의 재현 범위는 **가공된 결과표 기반의 포트폴리오 그림과 해석 재현**입니다.

---

## 11. Project Structure

```text
dominicks-price-elasticity-iv-dml/
├── README.md
├── requirements.txt
├── data/
│   └── README.md
├── notebooks/
│   ├── 01_results_overview.ipynb
│   ├── 02_fe_iv_baseline_results.ipynb
│   ├── 03_dynamic_iv_robustness.ipynb
│   └── 04_dml_validation_interpretation.ipynb
└── outputs/
    ├── figures/
    │   ├── dynamic_iv_cumulative_effects.png
    │   ├── fd_pliv_dml_own_price_effects.png
    │   ├── fe_iv_first_stage_strength.png
    │   ├── fe_iv_own_price_elasticity.png
    │   ├── fe_iv_sales_decomposition.png
    │   └── fe_iv_vs_dml_comparison.png
    └── tables/
        └── model_results/
            ├── cereal_only/
            ├── canned_soup_only/
            ├── bottled_juices_only/
            ├── cookies_only/
            ├── dynamic_checks/
            └── robustness/
```

`data/README.md`에는 원자료가 저장소에 포함되지 않는 이유와 결과 테이블 기반 재현 범위가 설명되어 있습니다.

`notebooks/`에는 포트폴리오용 결과 요약과 시각화 생성 노트북이 들어 있습니다.

`outputs/tables/model_results/`에는 카테고리별 FE-IV, Dynamic FE-IV, DML, robustness 결과 CSV가 들어 있습니다.

`outputs/figures/`에는 notebook에서 생성한 주요 그림이 저장되어 있습니다.

---

## 12. What This Project Demonstrates

이 프로젝트는 대용량 retail scanner 데이터에서 가격탄력성을 추정할 때 필요한 분석 사고를 보여줍니다.

첫째, 가격과 판매량의 단순 상관관계를 가격 효과로 해석하지 않고, 가격 내생성 문제를 먼저 정의했습니다.

둘째, 비용 변동을 도구변수로 사용해 FE-IV 구조를 설계했습니다.

셋째, 상품-매장 Fixed Effects와 week Fixed Effects를 사용해 고정적인 상품-매장 차이와 주차별 공통 충격을 통제했습니다.

넷째, first-stage strength를 확인해 도구변수가 가격을 충분히 설명하는지 점검했습니다.

다섯째, deal 변수와 rival 변수 등 통제 방식에 따라 계수가 얼마나 민감하게 움직이는지 확인했습니다.

여섯째, Dynamic FE-IV를 통해 현재 가격 효과와 누적 가격 효과가 다를 수 있음을 확인했습니다.

일곱째, FD-PLIV-DML을 통해 전통적인 FE-IV와 machine learning 기반 partial IV 결과를 비교했습니다.

마지막으로, 결과를 하나의 탄력성 숫자로 과장하지 않고, **가격 효과의 방향성, 사양 민감도, 식별 가정, robustness를 함께 제시하는 방식**으로 해석했습니다.

이 프로젝트의 핵심은 단순히 가격탄력성을 계산한 것이 아니라, **가격 효과를 추정할 때 어떤 내생성 문제와 검증 절차가 필요한지 보여준 것**입니다.
