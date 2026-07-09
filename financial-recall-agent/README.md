# Financial Recall Agent

금융 민원 1건을 출발점으로 삼아, 같은 원인으로 피해를 입었지만 아직 신고하지 않은 고객까지 찾아내고, 약관 근거·지급 원장·승인된 룰 실행 결과를 묶어 **운영자가 검토할 수 있는 리콜 조사 패키지**를 생성하는 LLM Agent 프로젝트입니다.

이 프로젝트의 핵심은 “LLM이 환불 여부를 판단한다”가 아닙니다. LLM은 민원을 이해하고 필요한 조사 흐름을 정리하는 데 사용하고, 실제 피해 고객 탐지·금액 계산·리콜 대상 확정은 **승인된 Rule Template, Product Config, SQL, Data Contract, Audit Log**로 통제합니다.

---

## 1. Overview

금융 민원은 보통 고객 1명의 불만으로 접수됩니다.

예를 들어 한 고객이 “체크카드 캐시백이 지급되지 않았다”고 문의하면, 일반적인 처리 흐름은 해당 고객의 거래와 혜택 지급 여부만 확인하는 데 그칠 수 있습니다.

하지만 실제 문제는 더 클 수 있습니다. 같은 상품, 같은 캠페인, 같은 지급 조건에서 동일한 오류가 발생했다면, 민원을 넣지 않은 다른 고객들도 같은 피해를 입었을 수 있습니다.

Financial Recall Agent는 이 문제를 다음처럼 정의했습니다.

> 민원 1건을 단일 고객 대응으로 끝내지 말고,  
> 같은 원인의 미신고 피해 고객까지 찾아내는 금융 소비자보호 워크플로우로 확장하자.

대표 MVP는 `H07 Reward/Cashback/Point/Mileage Missing` 유형입니다.

즉, 고객이 리워드·캐시백·포인트·마일리지 미지급을 주장하면, 시스템은 해당 민원을 상품 약관과 지급 원장에 연결하고, 승인된 룰을 실행해 같은 조건에서 지급이 누락된 고객을 탐지합니다.

대표 실행 결과는 다음과 같습니다.

| 항목 | 결과 |
|---|---:|
| 기준 민원 | `EVAL_BASE_0001` |
| Rule Template | `H07_REWARD_MISSING` |
| Product Config | `JB_SMART_CASHBACK_CHECK__2022-07__v2` |
| 피해 고객 수 | 44명 |
| 미신고 피해 고객 수 | 43명 |
| 추정 피해액 | 70,030원 |
| 자동 환불 허용 | False |
| 사람 검토 필요 | True |
| LLM SQL 생성 | False |
| 자유 SQL 실행 | False |

이 결과의 의미는 단순히 “44명을 찾았다”가 아닙니다.

중요한 점은 시스템이 임의로 고객을 찾은 것이 아니라, 승인된 bundle, 승인된 SQL, 검증된 product config, 약관 근거, data contract를 통과한 뒤에만 결과를 만들었다는 것입니다.

따라서 이 프로젝트의 결론은 다음과 같습니다.

> LLM은 금융 판단자가 아니라, 민원을 조사 가능한 구조로 정리하는 조정자다.  
> 실제 리콜 판단은 승인된 룰, 지급 원장, 약관 근거, 감사 가능한 실행 기록으로 통제해야 한다.

---

## 2. Problem & Objective

금융회사의 민원 처리는 고객 1명 단위로 끝나기 쉽습니다.

하지만 리워드 미지급, 수수료 오청구, 금리 적용 오류, 포인트 소멸 안내 누락 같은 문제는 한 고객에게만 발생하지 않을 수 있습니다. 상품 조건이나 지급 로직이 잘못되었다면 같은 조건을 가진 여러 고객에게 반복적으로 발생할 수 있습니다.

이때 단순 고객 응대 방식은 다음 문제를 만들 수 있습니다.

| 문제 | 왜 위험한가 |
|---|---|
| 민원 고객 1명만 처리 | 같은 피해를 입은 미신고 고객을 놓칠 수 있음 |
| LLM이 바로 판단 | 약관·원장·지급 조건을 검증하지 않고 단정할 위험 |
| 임의 SQL 생성 | 고객 데이터 전체를 잘못 조회하거나 과잉 탐지할 위험 |
| 룰과 상품 조건이 섞임 | 다른 상품으로 확장할 때 하드코딩이 늘어남 |
| 계산 결과만 출력 | 왜 이 고객이 대상인지 운영자가 검토하기 어려움 |
| 자동 보상 연결 | 잘못된 환급·중복 지급·내부 승인 누락 위험 |

따라서 이 프로젝트의 목적은 단순한 “민원 챗봇”이 아닙니다.

목표는 다음 세 가지입니다.

첫째, 민원 1건을 읽고 어떤 조사 유형인지 분류합니다.

둘째, 해당 유형에 맞는 승인된 rule bundle만 실행합니다.

셋째, 피해 고객 목록, 피해액, 약관 근거, 실행 로그, 검토 필요 사유를 하나의 evidence package로 생성합니다.

핵심 질문은 다음과 같습니다.

> 금융 민원 1건을 어떻게 동일 원인 피해 고객 탐지와 운영자 검토 가능한 리콜 패키지로 연결할 것인가?

---

## 3. Data

이 프로젝트는 공개 금융 데이터가 아니라, 금융 민원 업무를 모사한 synthetic dataset과 승인된 demo rule asset을 사용했습니다.

데이터는 단순히 모델 학습용 테이블이 아니라, 실제 리콜 조사를 재현하기 위한 업무 데이터 구조로 나누었습니다.

| 데이터 그룹 | 예시 | 역할 |
|---|---|---|
| 민원 데이터 | `complaint_id`, `customer_id`, `complaint_text`, `product_hint`, `channel` | 민원 유형 분류와 조사 시작점 |
| 고객 계약 데이터 | 고객별 상품 가입 정보, 계약 시작일, 상품 설정 | 해당 상품 조건이 적용되는 고객인지 확인 |
| 거래 원장 | 카드 사용 내역, 결제일, 금액, 가맹점/캠페인 코드 | 캐시백 지급 조건 충족 여부 확인 |
| 지급 원장 | 실제 캐시백/포인트 지급 기록 | 지급 누락 여부 확인 |
| 상품 설정 | 캐시백률, 월 한도, 제외 거래, 적용 기간 | Product Config 기반 계산 |
| 약관/정책 근거 | 상품 약관, 캠페인 조건, 내부 지급 기준 | Evidence package의 근거 문구 |
| 승인 실행 자산 | Rule Template, Product Config, SQL, Bundle | 임의 실행을 막는 통제 장치 |
| Audit Log | 실행 ID, 룰 ID, SQL hash, config hash, 결과 요약 | 사후 검토와 재현성 확보 |

MVP에서 사용한 대표 설정은 다음과 같습니다.

| 항목 | 값 |
|---|---|
| Rule Template | `H07_REWARD_MISSING` |
| Rule ID | `H07-REWARD-MISSING-TEMPLATE` |
| Product Config | `JB_SMART_CASHBACK_CHECK__2022-07__v2` |
| Data Contract | H07 reward missing investigation contract |
| SQL 실행 방식 | 승인된 SQL 파일만 실행 |
| LLM SQL 생성 | 금지 |
| 자동 환불 | 금지 |
| 최종 결정 | 운영자 검토 필요 |

여기서 중요한 설계는 Rule Template과 Product Config의 분리입니다.

`H07_REWARD_MISSING`은 “리워드/캐시백/포인트/마일리지 미지급”이라는 공통 조사 패턴입니다. 반면 `JB_SMART_CASHBACK_CHECK__2022-07__v2`는 특정 상품의 캐시백률, 지급 조건, 제외 거래, 적용 기간을 담은 설정입니다.

즉, 같은 H07 template을 유지하면서 상품이 바뀌면 Product Config만 추가하는 구조입니다.

---

## 4. Method / System Design

Financial Recall Agent의 설계 원칙은 명확합니다.

> LLM은 민원을 이해하고 조사 흐름을 정리한다.  
> 고객 탐지와 금액 계산은 승인된 deterministic rule로만 수행한다.

전체 구조는 다음과 같습니다.

```text
민원 1건 입력
   ↓
민원 유형 분류
   ↓
H07 여부 판단
   ↓
승인된 bundle 로드
   ↓
Rule Template 검증
   ↓
Product Config 검증
   ↓
Data Contract 검증
   ↓
SQL hash 검증
   ↓
승인된 SQL 실행
   ↓
피해 고객 / 미신고 고객 / 피해액 계산
   ↓
약관 근거 연결
   ↓
Evidence Package 생성
   ↓
Safety Gate
   ↓
Human Review Queue
   ↓
Audit Log 기록
```

### 4.1 LLM의 역할

LLM은 민원 텍스트를 읽고 조사 흐름을 정리하는 데 사용합니다.

예를 들어 고객이 이렇게 말할 수 있습니다.

```text
지난달 카드 혜택이 들어와야 하는데 캐시백이 안 들어온 것 같습니다.
앱에서는 조건을 채운 것 같은데 지급 내역이 없습니다.
확인 부탁드립니다.
```

LLM 또는 router는 이 민원이 H07 리워드/캐시백 미지급 유형인지 판단하고, 어떤 추가 확인이 필요한지 정리할 수 있습니다.

하지만 LLM이 하지 않는 일은 명확합니다.

| LLM이 하지 않는 일 | 이유 |
|---|---|
| SQL 생성 | 고객 원장 전체를 임의 조회하면 위험 |
| 피해 고객 확정 | 지급 조건과 원장 검증이 필요 |
| 피해액 계산 | 승인된 계산 로직으로 재현 가능해야 함 |
| 자동 환불 판단 | 내부 승인과 사람 검토 필요 |
| 약관 조건 임의 변경 | 승인된 Product Config와 policy evidence가 기준 |

즉, LLM은 조사 조정자이고, 최종 계산자는 아닙니다.

### 4.2 Rule Template과 Product Config 분리

초기 구조가 H07 Smart Cashback 전용으로 하드코딩되면, 상품이 바뀔 때마다 코드를 수정해야 합니다.

이를 막기 위해 공통 조사 패턴과 상품별 조건을 분리했습니다.

| 구분 | 역할 | 예시 |
|---|---|---|
| Rule Template | 공통 조사 패턴 | 리워드/캐시백/포인트/마일리지 미지급 대사 |
| Product Config | 상품별 지급 조건 | 캐시백률, 월 한도, 제외 거래, 캠페인 코드 |
| Approved SQL | 원장 대사 실행 로직 | 지급 조건 충족 고객 중 미지급 고객 조회 |
| Bundle | 승인된 실행 조합 | template + config + SQL + data contract |

이 구조의 장점은 확장성입니다.

새 상품이 추가되어도 `H07_REWARD_MISSING` template을 그대로 사용하고, 해당 상품의 Product Config만 추가하면 됩니다.

### 4.3 Approved Bundle

Financial Recall Agent는 아무 rule이나 실행하지 않습니다.

실행 전 bundle을 검증합니다.

Bundle은 다음 정보를 묶습니다.

| 항목 | 확인 내용 |
|---|---|
| `rule_template_id` | 승인된 template인지 |
| `rule_id` | registry에 존재하고 status가 approved인지 |
| `product_config_id` | 허용된 product config인지 |
| `sql_path` | 승인된 SQL 파일인지 |
| `sql_sha256` | SQL 파일이 변경되지 않았는지 |
| `data_contract_id` | 필요한 컬럼과 테이블이 맞는지 |
| `policy_basis_id` | 연결할 약관/정책 근거가 있는지 |
| `approval_status` | 운영 승인 상태인지 |

이 검증을 통과하지 못하면 rule은 실행되지 않습니다.

### 4.4 Data Contract

금융 원장 조회에서 가장 위험한 문제 중 하나는 데이터 구조가 바뀌었는데도 기존 로직이 계속 실행되는 것입니다.

예를 들어 지급 원장 컬럼명이 바뀌거나, campaign code가 누락되거나, 거래일 기준이 달라졌는데도 SQL이 실행되면 잘못된 대상자가 나올 수 있습니다.

그래서 실행 전에 data contract를 확인합니다.

| 검증 항목 | 예시 |
|---|---|
| 필수 테이블 존재 | complaints, card_contracts, transactions, reward_postings |
| 필수 컬럼 존재 | customer_id, product_id, transaction_date, amount, reward_paid |
| 날짜 범위 유효성 | 캠페인 적용 기간과 거래 기간 확인 |
| 상품 config 적용 가능성 | product_id, config_id, campaign_code 확인 |
| 결과 스키마 | affected_customer_count, harm_amount 등 필수 output 확인 |

### 4.5 Evidence Package

최종 결과는 숫자만 출력하지 않습니다.

운영자가 검토할 수 있도록 evidence package를 생성합니다.

| 구성 요소 | 설명 |
|---|---|
| Complaint Summary | 민원 원문과 요약 |
| Route Result | H07로 분류된 이유 |
| Policy Basis | 약관/정책 근거 문구 |
| Rule Template ID | 사용한 공통 조사 template |
| Product Config ID | 적용한 상품별 지급 조건 |
| SQL Hash | 실행한 승인 SQL의 hash |
| Affected Customer List | 피해 후보 고객 목록 |
| Unreported Customer List | 민원 미제기 피해 후보 |
| Harm Amount | 고객별/총 피해액 |
| Supporting Evidence | 대상자 판정 근거 |
| Missing Evidence | 아직 확인이 필요한 정보 |
| Safety Gate Result | 자동 환불 금지, 사람 검토 필요 |
| Audit Log | 실행 ID, 시각, 입력/출력 요약 |

이 구조 덕분에 운영자는 “AI가 그렇게 말했다”가 아니라, 어떤 약관과 어떤 원장 조건으로 해당 고객이 대상이 되었는지 확인할 수 있습니다.

---

## 5. Implementation

이 프로젝트는 단순 notebook이 아니라, 승인된 rule을 안전하게 실행하는 workflow로 구현했습니다.

주요 모듈은 다음과 같습니다.

| 모듈 | 역할 | 쉽게 말하면 |
|---|---|---|
| `core/bundle_loader.py` | 승인 bundle 로드와 검증 | 허용된 조합만 실행 |
| `core/artifact_hash.py` | SQL/config hash 계산 | 실행 자산 위변조 확인 |
| `core/data_contract.py` | 입력 데이터 스키마 검증 | 필요한 테이블/컬럼 확인 |
| `core/runtime_controls.py` | 금지 동작 차단 | LLM SQL, 자동 환불, placeholder rule 차단 |
| `templates/h07_reward_missing/` | H07 공통 조사 로직 | 캐시백/포인트 미지급 대사 패턴 |
| `rules/registry` | 승인 rule 목록 | 어떤 rule이 실행 가능한지 관리 |
| `product_configs/` | 상품별 지급 조건 | 캐시백률, 한도, 제외 거래 |
| `sql/approved/` | 승인된 SQL | deterministic ledger reconciliation |
| `policy_rag/` | 약관/정책 근거 | report에 연결할 근거 문구 |
| `interfaces/cli/` | 데모 실행 CLI | smoke test와 포트폴리오 실행 |
| `evaluation/` | 테스트와 평가 | routing, safety, evidence 검증 |

실행 흐름은 다음과 같습니다.

```text
1. 민원 record 입력
2. router가 H07 여부 판단
3. approved bundle 로드
4. rule registry 검증
5. product config 검증
6. SQL hash 검증
7. data contract 검증
8. 승인 SQL 실행
9. 피해 고객과 피해액 계산
10. 약관 근거 연결
11. evidence package 생성
12. safety gate 통과 여부 기록
13. audit log append
```

이 프로젝트에서 의도적으로 금지한 것도 있습니다.

| 금지한 것 | 이유 |
|---|---|
| LLM-generated SQL | 고객 원장에 대한 임의 조회 위험 |
| Free-form SQL | 승인되지 않은 계산 로직 실행 위험 |
| Automatic refund | 잘못된 환급·중복 보상 위험 |
| Placeholder rule execution | 데모용 임시 rule이 운영 결과로 쓰이는 위험 |
| Product config 임의 변경 | 상품 조건이 코드 밖에서 승인되어야 함 |
| Policy 없는 계산 결과 | 약관 근거 없는 리콜 판단 위험 |

---

## 6. Evaluation

이 프로젝트의 평가는 단순 정확도보다 **금융 업무에서 안전하게 실행 가능한가**를 중심으로 설계했습니다.

대표 smoke test 결과는 다음과 같습니다.

```text
complaint_id: EVAL_BASE_0001
rule_id: H07-REWARD-MISSING-TEMPLATE
rule_template_id: H07_REWARD_MISSING
product_config_id: JB_SMART_CASHBACK_CHECK__2022-07__v2
affected_customer_count: 44
unreported_customer_count: 43
total_harm_amount: 70030
decision_status: REQUIRES_HUMAN_CONFIRMATION
human_review_required: True
automatic_refund_allowed: False
used_private_ground_truth: False
llm_generated_sql: False
free_form_sql_allowed: False
```

### 6.1 Business Result

| 항목 | 결과 | 해석 |
|---|---:|---|
| 기준 민원 | 1건 | 고객 1명의 미지급 문의 |
| 피해 고객 | 44명 | 같은 조건에서 지급 누락 가능성이 있는 고객 |
| 미신고 피해 고객 | 43명 | 민원을 넣지 않았지만 같은 피해 가능성이 있는 고객 |
| 총 피해액 | 70,030원 | 지급 원장 대사 기준 추정 금액 |
| 자동 환불 | False | 운영자 검토 전 보상 금지 |
| 사람 검토 | True | 약관/원장/대상자 확인 필요 |

이 결과는 민원 1건이 단순 고객 응대가 아니라, 동일 원인 피해 고객 탐지로 확장될 수 있음을 보여줍니다.

### 6.2 Safety Evaluation

| 검증 항목 | 기대 결과 | 의미 |
|---|---|---|
| Approved bundle만 실행 | 통과 | 승인된 rule/config/SQL 조합만 허용 |
| SQL hash 검증 | 통과 | SQL 파일 변경 여부 확인 |
| Product config 검증 | 통과 | 상품 지급 조건의 승인 여부 확인 |
| Data contract 검증 | 통과 | 필요한 컬럼과 결과 스키마 확인 |
| Placeholder rule 차단 | 통과 | 임시 rule이 실행되지 않도록 방지 |
| LLM SQL 금지 | 통과 | LLM이 원장 조회 로직을 만들지 않음 |
| Free-form SQL 금지 | 통과 | 승인되지 않은 SQL 실행 차단 |
| Automatic refund 금지 | 통과 | 결과가 바로 보상으로 이어지지 않음 |
| Human review gate | 통과 | 운영자 확인 후 후속 조치 가능 |
| Audit log append | 통과 | 실행 근거와 결과 재현 가능 |

### 6.3 Routing Evaluation

민원 router는 모든 민원을 H07로 보내면 안 됩니다.

예를 들어 단순 앱 문의, 상담 요약, 감정적인 불만, 상품 정보 부족, H07이 아닌 수수료/금리/결제 문제는 곧바로 rule을 실행하지 않고 manual review 또는 다른 queue로 보내야 합니다.

평가 데이터는 다음 유형을 섞어 구성했습니다.

| Case Type | 목적 |
|---|---|
| 명확한 H07 미지급 주장 | approved rule 실행 여부 확인 |
| 애매한 혜택 문의 | 무리한 rule 실행 방지 |
| 비-H07 민원 | 다른 queue 또는 manual review |
| 감정적/불완전한 민원 | clarification 또는 manual review |
| 상품 힌트 부족 | product verification 필요 |
| 상담원 요약형 민원 | 간접 표현에서 route 판단 |

핵심은 recall만 높이는 것이 아니라, 잘못된 rule 실행을 막는 것입니다.

### 6.4 Evidence Quality

이 프로젝트에서 중요한 품질 기준은 결과 숫자보다 **왜 이 결과가 나왔는지 설명 가능한가**입니다.

| 항목 | 확인 내용 |
|---|---|
| 약관 근거 연결 | 캐시백 지급 조건과 제외 조건이 evidence에 포함되는가 |
| Rule Template 기록 | 공통 조사 패턴이 명확히 남는가 |
| Product Config 기록 | 적용 상품 조건이 명확히 남는가 |
| SQL Hash 기록 | 어떤 SQL로 계산했는지 재현 가능한가 |
| 고객별 피해액 | 총액뿐 아니라 고객별 산출 근거가 있는가 |
| Supporting/Missing Evidence | 근거와 부족한 정보가 분리되는가 |
| Safety Gate | 자동 환불 금지와 사람 검토 필요가 표시되는가 |

---

## 7. Key Design Decisions

### 7.1 민원 챗봇이 아니라 리콜 조사 workflow로 정의했다

금융 민원은 고객 응대만으로 끝나면 안 되는 경우가 있습니다.

한 고객의 미지급 민원은 같은 상품 조건을 가진 다른 고객의 피해 신호일 수 있습니다. 그래서 이 프로젝트는 “민원 답변 생성”이 아니라 “동일 원인 피해 고객 탐지와 운영자 검토 패키지 생성”으로 문제를 재정의했습니다.

### 7.2 LLM을 판단자가 아니라 조사 조정자로 제한했다

LLM은 민원 텍스트를 읽고 H07 가능성을 파악하거나, 약관 근거를 요약하는 데 유용합니다.

하지만 LLM이 고객 원장을 직접 조회하거나, SQL을 만들거나, 환불 여부를 판단하면 위험합니다. 그래서 LLM은 조사 흐름을 돕는 역할로 제한하고, 실제 계산은 승인된 rule과 SQL만 사용했습니다.

### 7.3 Rule Template과 Product Config를 분리했다

초기 H07 Smart Cashback 전용 구조는 빠르게 만들 수 있지만, 상품이 바뀔 때마다 코드가 늘어납니다.

그래서 “리워드 미지급 대사”라는 공통 template과 “특정 상품 지급 조건”인 product config를 분리했습니다. 이 구조 덕분에 새로운 캐시백 상품이나 포인트 상품이 추가되어도 template을 재사용할 수 있습니다.

### 7.4 승인된 bundle만 실행되도록 했다

금융 데이터 조회는 실행 자산 통제가 중요합니다.

Rule, Product Config, SQL, Data Contract, Policy Basis를 bundle로 묶고, 승인 상태와 hash를 검증한 뒤에만 실행하도록 했습니다. 이렇게 해야 운영자가 승인하지 않은 로직이 고객 데이터에 적용되는 것을 막을 수 있습니다.

### 7.5 결과를 자동 보상으로 연결하지 않았다

피해 고객과 피해액이 계산되더라도, 결과는 자동 환불로 이어지지 않습니다.

금융 보상에는 약관 해석, 예외 거래, 고객별 상황, 내부 승인, 법무/준법 검토가 필요할 수 있기 때문입니다. 따라서 결과는 human review queue로 보내고, evidence package를 통해 담당자가 확인할 수 있게 했습니다.

### 7.6 Audit Log를 핵심 산출물로 만들었다

금융 업무에서는 결과만큼 “어떻게 그 결과가 나왔는가”가 중요합니다.

그래서 실행 ID, rule ID, template ID, product config ID, SQL hash, data contract ID, affected count, harm amount, safety gate 결과를 audit log에 남겼습니다. 이를 통해 나중에 같은 입력과 같은 실행 자산으로 결과를 재현할 수 있습니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 H07 캐시백 미지급 데모처럼 시작했습니다.

하지만 개발하면서 핵심은 “캐시백 미지급을 한 번 찾는 것”이 아니라, 금융회사에서 확장 가능한 리콜 조사 구조를 만드는 것이라는 점이 분명해졌습니다.

첫 번째 전환점은 하드코딩 제거였습니다. Smart Cashback 하나만 처리하는 코드는 데모에는 빠르지만, 다른 포인트·마일리지·캐시백 상품으로 확장하기 어렵습니다. 그래서 H07 Reward Missing template과 Product Config를 분리했습니다.

두 번째 전환점은 SQL 통제였습니다. LLM Agent라는 이름 때문에 LLM이 SQL을 만들어 원장을 조회하게 하고 싶어질 수 있지만, 금융 원장에서는 위험합니다. 그래서 SQL은 반드시 승인된 파일만 실행하고, hash가 맞지 않으면 차단하도록 했습니다.

세 번째 전환점은 evidence 중심 설계였습니다. 단순히 “피해 고객 44명”이라고 출력하면 운영자가 믿기 어렵습니다. 그래서 약관 근거, product config, SQL hash, 고객별 지급 누락 근거, missing evidence, safety gate를 함께 묶은 evidence package로 정리했습니다.

네 번째 전환점은 자동 보상 금지였습니다. 리콜 후보를 잘 찾는 것과 실제 환급을 승인하는 것은 다른 문제입니다. 그래서 `automatic_refund_allowed=False`, `human_review_required=True`를 명시적으로 결과에 포함했습니다.

최종적으로 Financial Recall Agent는 “금융 민원 챗봇”이 아니라, **민원 1건을 동일 피해 고객 탐지와 내부 검토 패키지로 확장하는 controlled investigation engine**으로 정리되었습니다.

---

## 9. Limitations

이 프로젝트는 포트폴리오용 MVP이며, 실제 금융회사 운영에 적용하려면 추가 검증이 필요합니다.

첫째, 데이터는 synthetic dataset 기반입니다. 실제 금융회사 원장에서는 거래 취소, 부분 지급, 소급 조정, 예외 승인, 고객별 상품 변경 등 더 복잡한 케이스가 존재합니다.

둘째, MVP는 H07 Reward/Cashback/Point/Mileage Missing 유형에 집중했습니다. 수수료 오청구, 금리 오류, 환율 스프레드 고지 누락 등 다른 유형은 별도 template과 product config가 필요합니다.

셋째, 약관 문서와 내부 지급 정책의 버전 관리가 더 필요합니다. 실제 운영에서는 상품 약관 변경일, 공시 버전, 내부 운영 지침 버전이 모두 audit에 남아야 합니다.

넷째, 민원 router의 오분류 가능성이 있습니다. 애매한 민원은 rule을 무리하게 실행하지 않고 product verification 또는 manual review로 보내야 합니다.

다섯째, 피해액 계산은 approved SQL 기준의 추정입니다. 실제 보상 전에는 고객별 예외 거래, 이미 지급된 조정액, 중복 환급 여부를 확인해야 합니다.

여섯째, 현재 결과는 자동 환불로 연결하지 않습니다. 실제 운영에서는 승인 workflow, 권한 관리, 고객 통지, 회계 처리, 이의제기 대응이 필요합니다.

일곱째, LLM이 약관 근거를 요약할 때도 hallucination을 막아야 합니다. 실제 서비스에서는 약관 문구 citation, version pinning, retrieval evaluation이 필요합니다.

---

## 10. How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run H07 smoke test

대표 H07 리워드 미지급 데모를 실행합니다.

```bash
python -m src.recall_agent.interfaces.cli.h07_reward_missing_demo EVAL_BASE_0001 --json
```

기대되는 핵심 출력은 다음과 같습니다.

```text
affected_customer_count: 44
unreported_customer_count: 43
total_harm_amount: 70030
decision_status: REQUIRES_HUMAN_CONFIRMATION
human_review_required: True
automatic_refund_allowed: False
llm_generated_sql: False
free_form_sql_allowed: False
```

### Run tests

```bash
python -m pytest tests -q
```

### Recommended local checks

```bash
python -m pytest tests -q
python -m src.recall_agent.interfaces.cli.h07_reward_missing_demo EVAL_BASE_0001 --json
```

---

## 11. Project Structure

```text
financial-recall-agent/
├── README.md
├── requirements.txt
├── data/
│   └── demo/
│       ├── datasets/
│       │   ├── complaints.csv
│       │   ├── card_contracts.csv
│       │   ├── transactions.csv
│       │   └── reward_postings.csv
│       ├── rules/
│       │   ├── rule_registry.json
│       │   ├── product_configs/
│       │   ├── bundles/
│       │   └── data_contracts/
│       ├── policy_rag/
│       │   └── policy_basis.json
│       └── audit/
├── sql/
│   └── approved/
│       └── h07_reward_missing.sql
├── src/
│   └── recall_agent/
│       ├── core/
│       │   ├── artifact_hash.py
│       │   ├── bundle_loader.py
│       │   ├── data_contract.py
│       │   └── runtime_controls.py
│       ├── templates/
│       │   └── h07_reward_missing/
│       ├── policy/
│       ├── evidence/
│       ├── interfaces/
│       │   └── cli/
│       └── evaluation/
├── tests/
│   ├── test_bundle_validation.py
│   ├── test_data_contract.py
│   ├── test_h07_reward_missing.py
│   ├── test_runtime_controls.py
│   └── test_evidence_package.py
└── reports/
    └── demo_outputs/
```

실제 저장소 구조가 다르면 현재 폴더명과 파일명에 맞게 조정하면 됩니다.

---

## 12. What This Project Demonstrates

이 프로젝트는 LLM Agent를 금융 민원 업무에 안전하게 적용하기 위한 엔지니어링 설계를 보여줍니다.

첫째, 민원 1건을 고객 1명 응대로 끝내지 않고, 동일 원인 피해 고객 탐지 문제로 확장했습니다.

둘째, LLM을 SQL 생성자나 환불 판단자가 아니라, 민원 해석과 조사 조정 역할로 제한했습니다.

셋째, H07 Reward Missing을 Rule Template으로 일반화하고, 상품별 지급 조건은 Product Config로 분리했습니다.

넷째, 승인된 bundle, SQL hash, product config hash, data contract를 통과한 경우에만 원장 조회가 실행되도록 했습니다.

다섯째, 피해 고객 수, 미신고 고객 수, 피해액만 출력하지 않고, 약관 근거와 audit log가 포함된 evidence package를 생성했습니다.

여섯째, `automatic_refund_allowed=False`, `human_review_required=True`를 명시해 자동 보상을 막고 운영자 검토를 전제로 설계했습니다.

일곱째, placeholder rule, free-form SQL, LLM-generated SQL, data contract mismatch 같은 위험한 실행 경로를 차단했습니다.

여덟째, 대표 smoke test에서 민원 1건으로 피해 고객 44명, 미신고 피해 고객 43명, 추정 피해액 70,030원을 탐지했습니다.

이 프로젝트의 핵심은 단순히 금융 민원 챗봇을 만든 것이 아니라, **민원 신호를 약관·원장·승인 룰·감사 로그가 연결된 리콜 조사 워크플로우로 바꾼 것**입니다.
