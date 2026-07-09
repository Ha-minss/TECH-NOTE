# TECH-NOTE

이 저장소는 데이터 분석, 머신러닝, 계량경제학/인과추론, NLP/LLM 기반 시스템 프로젝트를 모아둔 기술 포트폴리오입니다.

자세한 문제 정의, 데이터 설명, 구현 방식, 평가 결과, 한계는 각 프로젝트 폴더의 `README.md`에서 확인할 수 있습니다.


# Projects

## 1. Applied AI / LLM Systems

이 섹션의 프로젝트들은 LLM을 단순 답변 생성기가 아니라, 실제 업무 흐름 안에서 **텍스트를 이해하고, 근거를 정리하고, 사람이 검토할 수 있는 결과물로 바꾸는 컴포넌트**로 사용하는 데 초점을 둡니다.

핵심 관심사는 LLM이 무엇을 할 수 있는가보다, **LLM에게 어디까지 맡기고, 어디서 규칙 검증·데이터 확인·사람 검토로 제어해야 하는가**입니다.

---

### Financial Recall Agent

**Financial Recall Agent**는 금융 민원 1건에서 출발해, 같은 원인으로 피해를 본 고객을 탐지하고 검토용 증거 패키지를 생성하는 LLM 기반 금융 소비자보호 프로젝트입니다.

이 프로젝트는 LLM을 금융 판단자로 사용하지 않습니다. LLM은 민원 내용을 이해하고 가능한 이슈를 분류하는 데 사용되지만, 실제 고객 영향 범위 확인, 금액 계산, 보상 가능 여부 판단은 승인된 규칙, 거래 데이터 검증, 감사 로그, 사람 검토 절차로 분리했습니다.

핵심은 “LLM으로 답변을 생성하는 것”이 아니라, 금융 업무에서 필요한 **근거 확인, 재현 가능성, 감사 가능성, 사람 검토**를 중심에 둔 구조를 설계한 것입니다.

* 주요 기술/개념: LLM, RAG, Rule-based Verification, Audit Log, Human Review
* 프로젝트 폴더: [`financial-recall-agent`](./financial-recall-agent)

---

### StoreOps Triage Agent

**StoreOps Triage Agent**는 오프라인 매장의 결제 장애 문의를 구조화하고, 운영자가 확인해야 할 증거와 조치 방향을 정리하는 LLM 기반 운영 지원 프로젝트입니다.

이 프로젝트는 매장 문의를 단순 챗봇 답변으로 처리하지 않습니다. 같은 “결제 실패”라도 실제 원인은 단말기 설정, POS 연결, 승인 로그, VAN/PSP 응답, 카드사 응답 등 여러 시스템으로 나뉘기 때문입니다.

그래서 LLM은 증상 이해와 확인 항목 정리에 사용하고, 실제 판단은 읽기 전용 도구 조회 결과와 규칙 기반 검증을 통해 보조하도록 설계했습니다. 최종 목표는 운영자가 장애 원인을 더 빠르게 좁히고, 불필요한 이관이나 잘못된 안내를 줄이는 것입니다.

* 주요 기술/개념: LLM Agent, Tool Calling, RAG, Payment Operations, Safety Gate
* 프로젝트 폴더: [`storeops-triage-agent`](./storeops-triage-agent)

---

### Recover24

**Recover24**는 보이스피싱·금융사기 피해자의 진술을 바탕으로 피해 복구에 필요한 문서와 사건 요약을 생성하는 NLP/LLM 기반 문서 자동화 프로젝트입니다.

피해자는 사건 직후 어떤 정보를 어디에 제출해야 하는지 알기 어렵고, 은행이나 기관은 피해 경위, 송금 정보, 노출 정보, 증빙 자료를 구조화해서 확인해야 합니다. 이 프로젝트는 피해자의 자연어 진술과 입력 정보를 바탕으로 사건을 정리하고, 문서 생성 가능 여부를 점검한 뒤, 제출 가능한 형태의 자료를 만드는 흐름을 설계했습니다.

LLM은 피해 진술의 의미를 파악하고 누락된 정보를 확인하는 데 사용하지만, 문서 생성 전에는 충돌 정보, 필수 항목 누락, 안전한 제출 가능 여부를 별도로 검토하도록 구성했습니다.

* 주요 기술/개념: NLP, LLM, Information Extraction, Document Automation, Safety Check
* 프로젝트 폴더: [`recover24`](./recover24)

---

### Provider Directory Control Tower

**Provider Directory Control Tower**는 의료 제공자 정보의 정확성을 공식 데이터와 대조하고, 수정 필요 여부를 판단하는 운영형 데이터 품질 관리 프로젝트입니다.

의료 제공자 정보는 이름, 주소, 전화번호, 진료 상태처럼 작은 오류도 사용자 검색 경험과 운영 신뢰도에 영향을 줄 수 있습니다. 이 프로젝트는 기존 제공자 정보를 공식 출처와 비교해 변경 후보를 만들고, 자동 수정이 가능한 경우와 사람 검토가 필요한 경우를 분리합니다.

핵심은 검색 결과를 그대로 믿는 것이 아니라, 공식 출처 기반의 증거, 충돌 여부, 신뢰도 점수, 검토 라우팅을 함께 설계한 것입니다.

* 주요 기술/개념: Data Quality, Evidence Matching, Confidence Scoring, Review Routing
* 프로젝트 폴더: [`provider-directory-control-tower`](./provider-directory-control-tower)

---

## 2. Machine Learning / Credit Risk

이 섹션의 프로젝트들은 머신러닝을 단순 예측 정확도 문제가 아니라, 실제 의사결정자가 **누구를 먼저 검토하고, 어떤 변수를 신뢰하며, 어떤 구간에서 대응해야 하는지**로 연결하는 데 초점을 둡니다.

핵심 관심사는 모델 성능뿐 아니라, 데이터 누수 방지, 검증 방식, 위험 구간 설계, 피처 채택 여부, 운영 활용 가능성입니다.

---

### AMEX Credit Risk Decisioning

**AMEX Credit Risk Decisioning**은 신용카드 고객의 상환 불이행 위험을 예측하고, 이를 리스크팀의 월별 검토 우선순위로 변환한 머신러닝 프로젝트입니다.

이 프로젝트는 불이행 여부를 단순히 맞히는 분류 문제로만 보지 않았습니다. 실제 운영에서는 모든 고객을 동일하게 검토할 수 없기 때문에, 모델 점수를 바탕으로 어떤 고객을 먼저 확인해야 하는지가 더 중요합니다.

따라서 고객별 위험 점수를 만들고, 상위 위험 구간의 정밀도와 Lift를 확인한 뒤, 월별 검토 대상 구간을 어떻게 설정할 수 있는지까지 연결했습니다.

* 주요 기술/개념: LightGBM, XGBoost, CatBoost, Tabular MLP, Ranking, Top-K Evaluation
* 핵심 결과: 상위 위험 구간에서 높은 정밀도와 Lift를 확인하고, 위험 점수를 검토 우선순위로 해석
* 프로젝트 폴더: [`amex-credit-risk-decisioning`](./amex-credit-risk-decisioning)

---

### Xente Credit Feature Adoption

**Xente Credit Feature Adoption**은 상환 이력이 없는 고객군에서 거래 행동 변수가 신용평가 피처로 채택할 만큼 독립적인 위험 신호인지 검증한 프로젝트입니다.

처음 질문은 단순했습니다. “거래 이력이 없는 고객은 더 위험한가?” 하지만 분석 과정에서 문제는 더 복잡해졌습니다. 거래 행동 변수는 고객 위험 자체뿐 아니라 서비스 흐름, 상품군, 대출 공급자 구조와 강하게 얽혀 있었습니다.

그래서 이 프로젝트는 거래 행동 변수를 바로 핵심 신용평가 변수로 채택하기보다, 실제로 추가적인 예측 가치가 있는지 검증했습니다. 결과적으로 거래 행동 변수는 핵심 변수로 바로 채택하기보다는, 특정 고위험 세그먼트를 관찰하는 보조 변수로 활용하는 방향이 더 적절하다고 판단했습니다.

* 주요 기술/개념: LightGBM, Logistic Regression, Stratified Group K-Fold, Permutation Test, Feature Adoption
* 핵심 관점: 예측력이 있어 보이는 변수라도, 독립적인 의사결정 가치가 있는지 검증해야 함
* 프로젝트 폴더: [`xente-credit-feature-adoption`](./xente-credit-feature-adoption)

---

## 3. Econometrics / Causal Inference

이 섹션의 프로젝트들은 단순 상관관계나 전후 비교가 아니라, 정책·사회·시장 데이터에서 **어떤 비교가 의미 있는지, 어떤 가정 위에서 결과를 해석할 수 있는지**를 검토합니다.

핵심 관심사는 DID, Event Study, Fixed Effects, Robustness 검증, Placebo Test, 식별 가정, 해석 가능한 한계입니다.

---

### Thailand Policy Revenue Persistence

**Thailand Policy Revenue Persistence**는 소비지원 정책 이후 숙박·음식서비스업 매출 반응이 일시적 효과인지, 이후에도 남는 지속 수요 신호인지 분석한 프로젝트입니다.

정책 이후 매출이 올랐다고 해서, 그 매출을 곧바로 상환 여력으로 해석할 수는 없습니다. 정책성 소비는 단기적으로 매출을 밀어 올릴 수 있지만, 그 효과가 이후에도 지속되는지는 별도의 검증이 필요합니다.

이 프로젝트는 정책 노출 업종과 비교업종의 상대 흐름을 구성하고, Lag Model, Synthetic Comparator, Event Study를 활용해 정책 이후 반응이 언제 나타나고 얼마나 지속되는지 확인했습니다.

* 주요 기술/개념: Lag Model, Synthetic Comparator, Event Study, Robustness 검증
* 핵심 결과: 정책 이후 0~3개월 누적 상대반응에서 양의 신호를 확인
* 프로젝트 폴더: [`thailand-policy-revenue-persistence`](./thailand-policy-revenue-persistence)

---

### Korea SECA → Kyushu SO₂

**Korea SECA → Kyushu SO₂**는 한국 SECA Step 1 시행 이후 일본 규슈 지역의 해안·내륙 SO₂ 격차가 줄어들었는지 분석한 환경정책 인과추론 프로젝트입니다.

이 프로젝트는 해운 연료 규제가 규제 지역 내부뿐 아니라 바람을 따라 이동하는 대기질에도 영향을 줄 수 있는지 검토합니다. 이를 위해 관측소와 월 단위 데이터를 구성하고, 해안 지역과 내륙 지역의 변화 차이를 비교했습니다.

DID, Fixed Effects, Event Study, Robustness 검증을 통해 정책 이후 SO₂ 변화 방향을 점검했으며, 주요 사양에서 해안 지역의 SO₂가 상대적으로 낮아지는 방향성을 확인했습니다.

* 주요 기술/개념: DID, Event Study, Fixed Effects, Robustness 검증
* 핵심 관점: 환경정책 효과는 단순 전후 비교보다 적절한 비교집단과 사전 추세 점검이 중요함
* 프로젝트 폴더: [`causal-inference-seca`](./causal-inference-seca)

---

### Refugee Inflows → Crime Rates

**Refugee Inflows → Crime Rates**는 난민 유입 규모와 범죄율 변화 사이의 관계를 국가-연도 패널 데이터로 분석한 사회 데이터 프로젝트입니다.

난민과 범죄율의 관계는 사회적으로 민감한 주제이기 때문에, 단일 회귀 결과만으로 강한 결론을 내리면 위험합니다. 이 프로젝트는 국가별 고정 특성, 연도별 공통 충격, 국가별 추세, 선행·후행 관계를 함께 검토하면서 결과가 얼마나 안정적인지 확인했습니다.

주요 결과는 난민 유입과 여러 범죄 지표 사이에서 일관되고 강한 양의 관계를 확인하기 어렵다는 것입니다. 특히 일부 상관관계는 추가적인 추세 통제를 넣으면 약해졌습니다.

* 주요 기술/개념: Panel Data, Fixed Effects, Dynamic Check, Robustness 검증
* 핵심 관점: 민감한 사회적 주장은 단일 계수가 아니라 여러 검증과 제한적인 해석이 필요함
* 프로젝트 폴더: [`refugees-crime-panel`](./refugees-crime-panel)

---

### Dominick's Price Elasticity IV-DML

**Dominick's Price Elasticity IV-DML**은 소매 스캐너 데이터를 활용해 가격 변화가 판매량에 미치는 영향을 추정한 가격탄력성 분석 프로젝트입니다.

가격과 판매량의 관계는 단순 회귀로 해석하기 어렵습니다. 가격은 수요 변화, 프로모션, 점포 특성, 상품 특성과 함께 움직일 수 있기 때문입니다. 따라서 이 프로젝트는 고정효과, IV, DML 기반 접근을 비교하면서 가격탄력성 추정치가 방법론과 통제 방식에 얼마나 민감한지 확인했습니다.

핵심은 하나의 탄력성 숫자를 제시하는 것이 아니라, 어떤 식별 전략과 Robustness 검증을 통해 그 숫자를 어디까지 신뢰할 수 있는지 설명하는 것입니다.

* 주요 기술/개념: Price Elasticity, Fixed Effects, IV, DML, Robustness 검증
* 핵심 관점: 가격탄력성은 단일 회귀 계수보다 식별 전략과 검증 과정이 중요함
* 프로젝트 폴더: [`dominicks-price-elasticity-iv-dml`](./dominicks-price-elasticity-iv-dml)


---

### Mobile Game LTV Production-Style ML Pipeline

Production-style ML pipeline for mobile game LTV prediction: raw data validation, modeling grain validation, feature generation, two-stage XGBoost final refit, prediction artifacts, model card, and UA business analysis.

* Key concepts: ML Pipeline, LTV Forecasting, Feature Engineering, Two-Stage Model, XGBoost, Optuna, Time-Based Validation, Business Analysis
* Project folder: [mobile-game-ltv-pipeline](./mobile-game-ltv-pipeline)

