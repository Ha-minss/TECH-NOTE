# 정책으로 오른 매출은 상환 여력인가

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

## Notebook Flow

1. `01_data_preparation.ipynb`: 월별 패널, 정책 강도, 분석 가능 범위 정리
2. `02_eda_visualization.ipynb`: 정책 기간과 숙박·음식서비스업 상대 흐름 확인
3. `03_modeling_event_study.ipynb`: lag model, synthetic comparator, event study
4. `04_validation_interpretation.ipynb`: placebo, permutation, robustness, 신용평가 해석
