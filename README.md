# TECH-NOTE

Dongha Park의 데이터 분석·머신러닝 포트폴리오 노트북 저장소입니다.

각 프로젝트는 README에서 분석 목적과 핵심 결과를 먼저 보고, `notebooks/` 폴더의 번호 순서대로 보면 됩니다.

#### **[1]   거래 이력 없음은 위험 신호인가: 상환 이력 없는 고객의 거래 행동 변수 검증**

일정: 2025. 11 ~ 2026. 02

한 줄 설명: 상환 이력이 없는 고객군에서 대출 전 거래 행동 변수가 신용평가 피처로 채택할 만큼 독립적인 위험 신호인지 검증한 프로젝트

핵심 성과: 거래 행동 변수의 핵심 피처 채택을 보류하고, 위험 신호가 서비스 흐름 ID 6, 리테일 상품군, 대출 공급자 구조와 강하게 얽혀 있음을 확인

팀 인원: 2인 프로젝트

기술 스택: Python, LightGBM, Stratified Group K-Fold, Permutation Test

GitHub: [GitHub / Project Page](https://github.com/Ha-minss/TECH-NOTE/tree/main/xente-credit-feature-adoption)

프로젝트페이지: [PARK-DONGHA-TECH-NOTES](https://park-dongha-portfolio-tech-notes.vercel.app/project/5)

**운영 제약을 반영한 구간 설계:** 전체 고객을 동일하게 심사할 수 없다는 전제하에 상위 위험 고객군부터 대응하는 기준 마련

- 핀테크 대출에서 상환 이력이 없는 고객을 단순히 “거래 이력 없음 = 고위험”으로 판단하기 어려운 문제를, 거래 행동 변수가 독립적인 신용위험 신호인지 검증하는 문제로 재정의했습니다.
- 대출 발행 시점을 기준으로 대출 이전 거래만 사용해 데이터 누수를 방지하고, Logistic Regression, LightGBM, Customer-level Stratified Group K-Fold, 변수군 제거 실험과 Permutation 검증으로 거래 행동 변수의 추가 가치를 비교했습니다.
- 검증 결과 거래 변수 추가 시 PR-AUC는 0.660 → 0.623, Top 10% Capture는 51.7% → 50.0%로 낮아져, 거래 행동 변수는 핵심 신용평가 변수로 채택하기보다 보조 관찰 변수로 두고 서비스 흐름 ID 6 등 고위험 세그먼트를 우선 관리하는 운영을 제안했습니다.

노트북 순서: `01_preprocessing` → `02_eda_visualization` → `03_modeling` → `04_validation_interpretation`

#### **[2]   정책으로 오른 매출은 상환 여력인가: 소비 지원 정책 이후 지속 수요 분석**

일정: 2026. 01 ~ 2026. 03

한 줄 설명: 소비지원 정책 이후 숙박·음식서비스업 지표의 상대 매출 반응이 당월 효과인지, 이후에도 남는 지속 신호인지 분석한 프로젝트

핵심 성과: 정책강도 Lag Model 기준 0~3개월 누적 상대반응 약 +18.1% 확인

팀 인원: 3인 프로젝트

기술 스택: Python, Statsmodels, Lag Model, Synthetic Comparator

GitHub: [GitHub](https://github.com/Ha-minss/TECH-NOTE/tree/main/thailand-policy-revenue-persistence)

프로젝트페이지: [PARK-DONGHA-TECH-NOTES](https://park-dongha-portfolio-tech-notes.vercel.app/project/6)

**운영 제약을 반영한 구간 설계:** 전체 고객을 동일하게 심사할 수 없다는 전제하에 상위 위험 고객군부터 대응하는 기준 마련

- 소비지원 정책으로 증가한 매출을 곧바로 지속 매출로 해석할 수 없는 문제를, 정책 이후 매출 반응이 얼마나 오래 유지되는지 검증하는 문제로 재정의했습니다.
- 숙박·음식서비스업을 정책 노출 업종으로 설정하고, 저노출 비교업종과의 로그 차이를 만든 뒤 정책강도 lag model과 synthetic comparator를 활용해 정책 전후 상대반응을 분석했습니다.
- 분석 결과 정책 당월 반응은 뚜렷하지 않았지만, 1~3개월 후 양의 반응이 나타났고 0~3개월 누적 반응은 약 +18.1%로 확인되어, 플랫폼 대출에서는 최근 매출 증가를 그대로 상환여력으로 반영하기보다 정책성 매출과 지속 매출을 분리해 해석해야 함을 도출했습니다.

노트북 순서: `01_data_preparation` → `02_eda_visualization` → `03_modeling_event_study` → `04_validation_interpretation`

#### **[3]   위험 점수는 누구를 먼저 보게 해야 하는가: 신용카드 불이행 예측의 검토 우선순위화**

일정: 2026.01 ~ 2026. 03

한 줄 설명: 아메리칸 익스프레스 고객 데이터를 기반으로 신용카드 상환 불이행 위험 점수를 만들고, 이를 리스크팀의 월별 검토 우선순위로 변환한 프로젝트

핵심 성과: Top 1% 정밀도 99.98%, Lift 3.86 / Top 5% 정밀도 84.79%, Lift 3.83

팀 인원: 3인 프로젝트

기술 스택: Python, LightGBM, XGBoost, CatBoost, Tabular MLP

GitHub: [GitHub / Project Page](https://github.com/Ha-minss/TECH-NOTE/tree/main/amex-credit-risk-decisioning)

프로젝트페이지: [PARK-DONGHA-TECH-NOTES](https://park-dongha-portfolio-tech-notes.vercel.app/project/4)

**운영 제약을 반영한 구간 설계:** 전체 고객을 동일하게 심사할 수 없다는 전제하에 상위 위험 고객군부터 대응하는 기준 마련

- 신용카드 상환 불이행 예측을 단순 분류 문제가 아닌 **리스크팀의 월별 검토 우선순위 선정 문제**로 재정의하고, 고객별 위험 점수를 검토 구간과 월별 검토 대상 목록으로 변환했습니다.
- 익명화된 고객-월 데이터를 **요약 통계, 시계열 변화, 최근 구간, 결측 패턴** 중심의 피처로 집계하고, LightGBM, XGBoost, CatBoost, Tabular MLP 기반 out of fold 앙상블을 통해 안정적인 위험 순위 점수를 생성했습니다.
- 상위 K% 검토 구간과 10분위 검증을 통해 위험 점수의 운영 활용 가능성을 확인했으며, **상위 1% 구간은 정밀도 99.98%, Lift 3.86, 상위 5% 구간은 정밀도 99.11%, Lift 3.83**을 보였습니다. 비용 가정에서 Top 17% 검토 구간이 가장 높은 정규화 순효익을 보임을 확인했습니다.

노트북 순서: `01_preprocessing` → `02_modeling` → `03_validation` → `04_scenario`
