# 거래 이력 없음은 위험 신호인가

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

## Notebook Flow

1. `01_preprocessing.ipynb`: 원자료 확인, 대출 1건 단위 분석 테이블 생성
2. `02_eda_visualization.ipynb`: 거래 이력, 상품군, 공급자, 서비스 흐름 ID 구조 확인
3. `03_modeling.ipynb`: 기본 모델과 거래 변수 추가 모델 비교
4. `04_validation_interpretation.ipynb`: score band, permutation, SHAP, 최종 채택 판단
