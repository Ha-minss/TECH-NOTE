# 위험 점수는 누구를 먼저 보게 해야 하는가

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

## Notebook Flow

1. `01_preprocessing.ipynb`: 고객-월 데이터를 고객 단위 피처 행렬로 변환
2. `02_modeling.ipynb`: AMEX metric, 모델 스택, OOF 앙상블, risk score 생성
3. `03_validation.ipynb`: decile, risk band, cumulative capture 검증
4. `04_scenario.ipynb`: Top-K review policy, 비용 가정, Top 17% 운영 기준
