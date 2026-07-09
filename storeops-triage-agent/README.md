# StoreOps Triage Agent

매장 결제 장애 문의를 받아 **운영자가 검토할 수 있는 원인 후보, 조회 근거, 다음 확인 항목, 안전한 안내 문구**로 정리하는 오프라인 결제 운영 triage agent입니다.

이 프로젝트의 핵심은 “LLM이 결제 장애 원인을 맞힌다”가 아닙니다. 가맹점주의 짧은 문의를 구조화하고, SOP/RAG에서 확인해야 할 항목을 찾고, 읽기 전용 운영 도구로 근거를 조회한 뒤, 근거가 충분할 때만 원인 후보를 제시하는 **evidence-first 운영 워크플로우**입니다.

---

## 1. Overview

오프라인 매장에서 결제가 실패하면 현장은 바로 멈춥니다.

사장님은 “결제가 안 돼요”, “단말기 승인 실패가 계속 떠요”, “POS에서 금액이 단말기로 안 넘어가요”처럼 짧게 문의합니다. 하지만 운영자가 확인해야 할 원인은 하나가 아닙니다.

같은 “결제 실패”라도 실제 원인은 다음처럼 갈라질 수 있습니다.

| 원인 후보 | 쉽게 말하면 |
|---|---|
| `duplicate_tid` | 새 단말기 설치 후 기존 단말기와 결제 식별값이 겹침 |
| `terminal_identifier_mismatch` | 현장 단말기 번호/시리얼과 등록 시스템 값이 다름 |
| `van_merchant_registration_missing` | VAN 또는 가맹점 번호 등록이 완료되지 않음 |
| `pos_front_connection_issue` | POS 결제 요청이 결제 단말기/Front로 전달되지 않음 |
| `clarification_required` | 문의가 너무 모호해 현장 추가 정보가 필요 |
| `tool_failure` | 필수 운영 데이터 조회가 실패해 원인 확정이 불가 |
| `temporal_conflict` | 사건 당시 기록과 현재 기록이 달라 시간축 검토 필요 |

StoreOps Triage Agent는 이 문제를 다음처럼 정의했습니다.

> 가맹점주의 결제 장애 문의를  
> 운영자가 검토 가능한 evidence-backed case brief로 바꾸자.

전체 흐름은 다음과 같습니다.

```text
가맹점 문의
→ 문의 유형 파싱
→ SOP/RAG 검색
→ 확인해야 할 data_need 선정
→ read-only tool 계획
→ SQLite fixture에서 운영 근거 조회
→ evidence record 생성
→ 원인 후보 판단
→ safety gate 적용
→ 운영자 검토용 case brief 생성
→ 평가/trace 저장
```

이 시스템은 결제 실행, 환불, 승인 취소, TID 변경, VAN 설정 변경 같은 민감한 조치를 수행하지 않습니다.

할 수 있는 일은 다음과 같습니다.

- 문의를 구조화한다.
- 어떤 운영 데이터를 확인해야 하는지 계획한다.
- 읽기 전용 도구로 근거를 조회한다.
- 근거가 있으면 원인 후보를 제시한다.
- 근거가 부족하거나 충돌하면 판단을 보류한다.
- 운영자에게 다음 확인 항목과 안전한 안내 문구를 제안한다.

따라서 이 프로젝트의 결론은 다음과 같습니다.

> 결제 장애 agent는 “원인을 맞히는 챗봇”이 아니라,  
> 현장 문의를 운영 근거와 안전 게이트가 붙은 검토 가능한 사건으로 바꾸는 triage workflow여야 한다.

---

## 2. Problem & Objective

매장 결제 장애는 일반적인 고객 문의보다 운영 리스크가 큽니다.

잘못 안내하면 사장님은 계속 결제를 재시도할 수 있고, 고객 앞에서 결제가 멈출 수 있으며, 운영팀은 VAN, 단말기 설치 대행, POS, 내부 설정 담당자 사이에서 원인을 찾느라 시간이 지연될 수 있습니다.

문제는 문의 문장만으로 원인을 확정하기 어렵다는 점입니다.

예를 들어 다음 두 문의는 비슷해 보이지만 확인해야 할 데이터가 다릅니다.

| 문의 | 먼저 봐야 할 데이터 |
|---|---|
| “새 단말기 설치 후 기존 단말기에서 카드 승인이 실패합니다.” | 단말기 목록, TID 설정, 개시 이력, 승인 실패 로그 |
| “POS에서 결제를 눌러도 단말기로 금액이 안 넘어갑니다.” | POS-Front 연결 로그, 요청 전달 실패, pairing 상태 |

따라서 이 프로젝트의 목표는 단순한 답변 생성이 아닙니다.

목표는 다음 네 가지입니다.

첫째, 가맹점 문의에서 결제 승인 장애인지, POS-Front 연동 문제인지, 추가 확인이 필요한 모호 문의인지 분류합니다.

둘째, SOP/RAG와 tool catalog를 기반으로 확인해야 할 data_need와 read-only tool을 계획합니다.

셋째, 조회된 운영 데이터를 evidence record로 바꾸고, 근거가 충분한 경우에만 원인 후보를 제시합니다.

넷째, 필수 데이터 조회 실패, 증거 부족, 시간축 충돌, 민감 조치 요청은 안전 게이트를 통해 `NEEDS_CLARIFICATION`, `DEGRADED_REVIEW`, `CONFLICT_REVIEW`로 보냅니다.

이 프로젝트가 막으려는 위험은 다음과 같습니다.

| 위험 | 방지 방식 |
|---|---|
| 근거 없이 원인 단정 | supporting evidence가 없으면 `likely` 판단 금지 |
| 결제/환불/설정 변경 | forbidden actions로 차단 |
| 필수 도구 실패에도 원인 판단 | `DEGRADED_REVIEW`로 전환 |
| 현장 설명과 시스템 기록 충돌 | `CONFLICT_REVIEW`로 전환 |
| 모호한 문의에 무리한 진단 | `NEEDS_CLARIFICATION`으로 전환 |
| LLM이 도구나 data_need를 발명 | prompt contract와 allowed catalog로 제한 |

---

## 3. Data

이 프로젝트는 실제 운영 데이터를 사용하지 않고, 오프라인 결제 장애를 모사한 50개 합성 운영 사건과 SQLite fixture를 사용했습니다.

중요한 점은 원인 정답을 raw operational table 안에 넣지 않았다는 것입니다. 운영 도구가 조회하는 DB에는 실제 운영 사실만 있고, 정답 label은 golden set과 평가 파일에만 있습니다.

즉, agent는 정답을 읽는 것이 아니라, 운영 fact를 조회하고 조합해 원인을 판단해야 합니다.

Canonical assets는 다음과 같습니다.

```text
data/fixtures/offline_payment_ops_synthetic_50.sqlite3
data/fixtures/offline_payment_ops_synthetic_50_manifest.json
data/golden/offline_payment_ops_cases_50.json
data/evaluation/retrieval_cases_50.json
data/evaluation/planner_cases_50.json
data/policies/offline_payment_ops/
data/tool_catalog/offline_payment_ops_tools.json
reports/synthetic_50_validation_report.md
reports/synthetic_50_validation_matrix.csv
```

합성 50개 케이스의 분포는 다음과 같습니다.

| Family | Case Type | 건수 | 기대 상태 |
|---|---|---:|---|
| S1 | `duplicate_tid` | 10 | `READY_FOR_REVIEW` |
| S2 | `terminal_identifier_mismatch` | 7 | `READY_FOR_REVIEW` |
| S3 | `van_merchant_registration_missing` | 7 | `READY_FOR_REVIEW` |
| S4 | `pos_front_connection_issue` | 7 | `READY_FOR_REVIEW` |
| S5 | `clarification_required` | 7 | `NEEDS_CLARIFICATION` |
| S6A | `required_tool_failure` | 4 | `DEGRADED_REVIEW` |
| S6B | `optional_tool_failure` | 3 | `READY_FOR_REVIEW` |
| S7 | `temporal_conflict` | 5 | `CONFLICT_REVIEW` |

합성 fixture의 row-level validation 결과는 50/50 통과했습니다.

| 검증 항목 | 결과 |
|---|---:|
| Total cases | 50 |
| Passed | 50 |
| Failed | 0 |

주요 테이블 row count는 다음과 같습니다.

| Table | Row count |
|---|---:|
| `stores` | 50 |
| `store_operator_access` | 50 |
| `terminals` | 86 |
| `tid_assignments` | 91 |
| `activation_events` | 22 |
| `approval_events` | 53 |
| `support_routes` | 38 |
| `terminal_identities` | 86 |
| `installation_events` | 12 |
| `van_registrations` | 14 |
| `pos_front_links` | 7 |
| `pos_front_connection_events` | 7 |
| `tool_failure_injections` | 7 |
| `scenarios` | 50 |
| `scenario_stores` | 50 |

SOP/RAG 문서는 5개입니다.

| Policy ID | 역할 |
|---|---|
| `SOP-PAY-OP-001` | 결제 승인 오류 초기 대응 |
| `SOP-PAY-OP-002` | 신규 단말기 설치 및 식별 정보 검증 |
| `SOP-PAY-OP-003` | 가맹점/VAN 등록 상태 점검 |
| `SOP-PAY-OP-004` | POS-Front 연동 및 통신 장애 점검 |
| `SOP-PAY-OP-005` | 불확실성·사람 검토·안전 수칙 |

---

## 4. Method / System Design

StoreOps Triage Agent의 설계 원칙은 명확합니다.

> 문의 문장만으로 원인을 단정하지 않는다.  
> 운영 데이터를 읽기 전용으로 조회하고, 근거가 있을 때만 원인 후보를 제시한다.

전체 구조는 다음과 같습니다.

```text
Merchant Message
   ↓
Case Parser
   ↓
Policy Retrieval
   ↓
Planner
   ↓
Read-only Tool Gateway
   ↓
Evidence Builder
   ↓
Reasoner
   ↓
Safety Gate
   ↓
Case Brief
   ↓
Evaluation / Trace
```

### 4.1 Case Parser

가맹점 문의를 읽고 결제 장애 유형과 부족한 현장 정보를 파악합니다.

Parser가 하는 일은 다음과 같습니다.

| 하는 일 | 예시 |
|---|---|
| 문의 유형 분류 | 결제 승인 실패, POS-Front 연결 문제 |
| merchant-observable missing field 추출 | 오류 시각, 단말기 위치, 오류 문구 등 |
| 내부 DB 사실 추론 금지 | TID 중복, VAN 등록 상태를 문장만 보고 단정하지 않음 |

Parser는 최종 원인을 판단하지 않습니다.

### 4.2 Policy Retrieval

문의 유형과 관련된 SOP 문서를 검색합니다.

예를 들어 신규 단말기 설치 후 기존 단말기 승인 실패 문의라면, 단말기 설치/식별 정보 검증 지침과 결제 승인 오류 지침이 중요합니다.

RAG는 답변을 만들기 위한 장식이 아니라, planner가 어떤 evidence를 확인해야 하는지 결정하는 기준으로 사용됩니다.

### 4.3 Planner

Planner는 SOP와 tool catalog를 보고 확인해야 할 `data_need`와 read-only tool을 고릅니다.

예를 들어 `duplicate_tid` 의심 상황에서는 다음 도구가 필요합니다.

| Data need | Tool |
|---|---|
| 단말기 목록 | `get_terminals` |
| 결제 식별 설정 | `get_tid_config` |
| 단말기 개시 이력 | `get_activation_history` |
| 승인 실패 로그 | `get_recent_approval_errors` |

Planner가 금지된 것도 있습니다.

| 금지된 행동 | 이유 |
|---|---|
| 새 data_need 발명 | 평가와 tool catalog 계약이 깨짐 |
| 새 tool 발명 | 실제 실행 가능한 도구가 아님 |
| 원인 확정 | planner는 조사 계획만 담당 |
| 결제/환불/설정 변경 요청 | 운영 안전 경계 위반 |

### 4.4 Read-only Tool Gateway

Tool Gateway는 SQLite fixture에서 운영 데이터를 조회합니다.

모든 도구는 읽기 전용입니다.

| Tool | 확인하는 것 |
|---|---|
| `get_store_info` | 매장 기본 정보와 운영 상태 |
| `get_terminals` | 매장 단말기 목록과 설치/활성화 시각 |
| `get_tid_config` | 단말기별 현재 또는 과거 TID/식별 설정 |
| `get_tid_history` | 사건 당시와 현재의 TID 설정 이력 |
| `get_terminal_identity` | 현장 단말기 번호/시리얼과 등록값 비교 |
| `get_installation_history` | 설치, 교체, 설정 변경 이력 |
| `get_activation_history` | 단말기 개시, 활성화, 결제 테스트 이력 |
| `get_recent_approval_errors` | 승인 실패 내역과 응답 문구 |
| `get_van_registration` | 가맹점 번호와 VAN 등록 상태 |
| `get_pos_front_connection_logs` | POS-Front 연결, 요청 전달, 타임아웃 로그 |
| `get_support_route` | 원인 평가 후 담당자 검토 경로 |

S6A/S6B 케이스에서는 tool failure injection을 통해 필수 도구 실패와 선택 도구 실패를 구분했습니다.

### 4.5 Evidence Builder

조회 결과는 바로 원인으로 변환되지 않습니다.

먼저 evidence record로 바꿉니다.

```text
evidence_id
source_tool
source_record_id
fact_type
normalized_value
observed_at
supports
contradicts
sensitivity
```

예를 들어 `terminal_identity_mismatch` evidence는 현장 단말기 번호와 등록 시스템 번호가 다르다는 사실을 담습니다.

`temporal_conflict` evidence는 사건 당시에는 TID가 중복되어 있었지만 현재는 정상화되어 있다는 사실을 담습니다. 이 경우 현재 값만 보면 원인을 놓칠 수 있으므로, 시간축 evidence가 중요합니다.

### 4.6 Reasoner

Reasoner는 evidence를 모아 원인 후보를 판단합니다.

단, supporting evidence가 없으면 `likely` 원인을 표시하지 않습니다.

| Evidence pattern | Cause |
|---|---|
| 동일 매장 active TID 중복 + 승인 실패 로그 | `duplicate_tid` |
| 현장 단말기 번호/시리얼과 등록값 불일치 | `terminal_identifier_mismatch` |
| VAN 등록 상태 inactive/pending/missing + 등록 관련 승인 오류 | `van_merchant_registration_missing` |
| POS-Front pairing/request delivery 실패 로그 | `pos_front_connection_issue` |
| 사건 당시 TID 중복, 현재는 정상 | `temporal_conflict` |

### 4.7 Safety Gate

Safety Gate는 최종 상태를 결정합니다.

| 조건 | 상태 |
|---|---|
| 원인 후보와 supporting evidence가 있음 | `READY_FOR_REVIEW` |
| 문의가 모호하고 merchant 정보가 부족함 | `NEEDS_CLARIFICATION` |
| 필수 tool이 실패함 | `DEGRADED_REVIEW` |
| evidence가 서로 충돌함 | `CONFLICT_REVIEW` |
| 원인 후보가 없고 근거도 부족함 | `DEGRADED_REVIEW` |

Safety Gate의 목적은 원인을 많이 맞히는 것이 아니라, 근거 없는 단정과 위험한 조치를 막는 것입니다.

---

## 5. Implementation

이 프로젝트는 domain logic, core workflow, LLM components, evaluation을 분리해 구현했습니다.

주요 모듈은 다음과 같습니다.

| 모듈 | 역할 | 쉽게 말하면 |
|---|---|---|
| `core/contracts.py` | 상태, evidence, tool response, case brief 타입 정의 | 전체 시스템의 계약 |
| `core/planner.py` | rule-backed deterministic planner | 어떤 데이터를 봐야 하는지 결정 |
| `core/safety.py` | generic safety gate | 근거 부족/충돌/도구 실패 상태 전환 |
| `domains/offline_payment_ops/parser.py` | 결제 장애 문의 파싱 | 문의를 사건 후보로 정리 |
| `domains/offline_payment_ops/evidence_rules.py` | tool 결과를 evidence로 변환 | 조회 결과를 근거 카드로 바꿈 |
| `domains/offline_payment_ops/reasoner_rules.py` | evidence 기반 원인 판단 | evidence pattern → cause |
| `domains/offline_payment_ops/safety_rules.py` | 금지 행동 정의 | 결제/환불/설정 변경 금지 |
| `domains/offline_payment_ops/tool_gateway.py` | SQLite read-only tool 실행 | 운영 fact 조회 |
| `domains/offline_payment_ops/workflow.py` | domain workflow 조립 | parser→planner→tool→evidence→brief |
| `llm/` | bounded LLM parser/planner/drafting | LLM을 계약 안에 제한 |
| `evals/` | deterministic/LLM 평가 runner | 50-case 평가와 smoke test |
| `observability/` | trace, metrics, serialization | 실행 기록과 지표 저장 |

실행 경로는 두 가지입니다.

### Deterministic path

규칙 기반 parser/planner/reasoner를 사용해 50개 synthetic dataset 전체를 평가합니다.

```text
Golden cases
→ OfflinePaymentWorkflow
→ SQLite read-only tools
→ Evidence
→ Reasoner
→ Safety Gate
→ Case Brief
→ Evaluation Report
```

### LLM path

LLM을 parser/planner/checklist/clarification/drafting에 일부 넣되, 같은 tool gateway와 safety gate를 사용합니다.

즉, LLM이 들어와도 다음 경계는 유지됩니다.

| 유지되는 경계 | 의미 |
|---|---|
| allowed data_need만 사용 | LLM이 임의 data_need를 만들 수 없음 |
| tool catalog 안의 tool만 사용 | LLM이 새 도구를 발명할 수 없음 |
| read-only tool만 실행 | 결제/환불/설정 변경 불가 |
| evidence 없는 원인 단정 금지 | supporting evidence 필요 |
| forbidden actions 차단 | 민감 조치 출력 방지 |

---

## 6. Evaluation

평가는 두 층으로 나누었습니다.

첫째, synthetic dataset 자체가 논리적으로 맞게 생성되었는지 확인했습니다.

둘째, agent가 해당 dataset에서 기대 상태와 원인을 맞히는지 평가했습니다.

### 6.1 Synthetic Dataset Validation

합성 데이터 검증 결과는 다음과 같습니다.

| 항목 | 결과 |
|---|---:|
| Total cases | 50 |
| Passed | 50 |
| Failed | 0 |

이 검증은 agent 성능 평가가 아니라, raw operational facts가 의도한 원인/상태 label과 논리적으로 일치하는지 확인하는 row-level validation입니다.

즉, 평가 데이터 자체가 깨져 있지 않은지 먼저 확인한 것입니다.

### 6.2 Deterministic Evaluation

Deterministic benchmark 결과는 다음과 같습니다.

| 지표 | 결과 |
|---|---:|
| Total cases | 50 |
| Passed cases | 38 |
| State accuracy | 0.90 |
| Cause accuracy | 0.98 |
| Abstention safety accuracy | 1.00 |
| Unsupported claim count | 0 |
| Tool failure recovery rate | 1.00 |
| Operator correction candidate count | 12 |

이 결과에서 가장 중요한 지표는 `unsupported_claim_count = 0`과 `abstention_safety_accuracy = 1.00`입니다.

즉, 시스템은 틀릴 수는 있지만, 근거 없이 원인을 단정하지 않도록 설계되어 있습니다.

38/50 통과는 완성도가 아주 높은 최종 운영 시스템이라는 뜻은 아닙니다. 특히 failing case는 대부분 required tool recall, clarification state, tool failure handling, temporal conflict 처리에서 발생했습니다.

대표 failing category는 다음과 같습니다.

| 실패 양상 | 의미 | 개선 방향 |
|---|---|---|
| S5 모호 문의에서 required tool 누락 | 문의가 짧을 때 baseline evidence 계획이 부족 | clarification 전 최소 조회 정책 보강 |
| S6A 필수 도구 실패 상태 차이 | 필수 tool failure와 clarification 우선순위 충돌 | safety transition 우선순위 조정 |
| S6B 선택 도구 실패에서 과도한 degraded 처리 | 핵심 evidence는 있는데 선택 tool 실패가 상태를 흔듦 | required/supporting/optional 분리 강화 |
| S7 시간축 충돌 누락 | 현재 설정과 사건 당시 설정을 분리해야 함 | incident-time evidence 우선순위 강화 |

이 점은 오히려 포트폴리오 관점에서 중요합니다. 단순히 “정확도 높음”이 아니라, 어떤 failure mode가 남아 있고 어떻게 개선해야 하는지 분석 가능한 구조이기 때문입니다.

### 6.3 LLM Smoke Test

Live LLM smoke test는 1개 케이스 기준으로 수행되었습니다.

| 지표 | 결과 |
|---|---:|
| Total cases | 1 |
| State accuracy | 1.00 |
| Cause accuracy | 1.00 |
| Required tool recall | 0.75 |
| Forbidden action safety | 1.00 |
| Evidence citation coverage | 1.00 |
| Clarification safety | 1.00 |
| Merchant response safety | 1.00 |
| LLM trace coverage | 1.00 |
| Fallback rate | 0.00 |
| Unsupported claim count | 0 |

LLM path는 원인과 상태는 맞췄지만, `get_activation_history`를 빠뜨려 required tool recall이 0.75였습니다.

이 결과는 LLM을 운영에 그대로 맡기면 안 되는 이유를 보여줍니다.

LLM은 문장을 잘 이해할 수 있지만, SOP가 요구하는 모든 필수 evidence를 빠짐없이 고르는 것은 별도로 검증해야 합니다. 그래서 이 프로젝트는 LLM path에도 tool catalog, allowed data_need, prompt contract, safety gate를 유지했습니다.

---

## 7. Key Design Decisions

### 7.1 결제 장애를 답변 생성 문제가 아니라 근거 수집 문제로 정의했다

가맹점주는 “결제가 안 된다”고 말하지만, 운영자는 단말기, TID, VAN 등록, 승인 로그, POS 연결 상태를 대조해야 합니다.

그래서 이 프로젝트는 “친절한 답변”보다 “어떤 근거를 확인했고, 그 근거로 어떤 원인 후보를 말할 수 있는가”에 초점을 맞췄습니다.

### 7.2 모든 tool을 읽기 전용으로 제한했다

결제 장애 대응에서 가장 위험한 것은 원인이 확정되지 않았는데 설정을 바꾸거나, 결제 취소/환불/외부 이관을 안내하는 것입니다.

따라서 tool gateway는 조회만 수행하고, config mutation, payment execution, refund, cancellation은 forbidden action으로 차단했습니다.

### 7.3 Planner와 Reasoner를 분리했다

Planner는 어떤 데이터를 봐야 하는지 결정합니다.

Reasoner는 조회된 evidence를 보고 원인 후보를 판단합니다.

이 둘을 분리한 이유는 계획 단계에서 원인을 먼저 단정하지 않기 위해서입니다. 먼저 필요한 근거를 확인하고, 그 뒤 evidence pattern으로 판단해야 운영 사고를 줄일 수 있습니다.

### 7.4 현재 상태와 사건 당시 상태를 분리했다

결제 장애는 시간축이 중요합니다.

현재 TID가 정상이라고 해서 사건 당시도 정상이라고 볼 수 없습니다. S7 케이스처럼 사건 당시에는 TID 중복이 있었지만 현재는 정상화되어 있을 수 있습니다.

그래서 `get_tid_history`와 incident-time evidence를 통해 현재 snapshot과 사건 당시 상태를 분리했습니다.

### 7.5 필수 도구 실패와 선택 도구 실패를 다르게 취급했다

필수 도구가 실패하면 원인을 확정하면 안 됩니다.

반면 선택 도구가 실패했더라도 핵심 evidence가 있으면 검토 가능한 상태로 남길 수 있습니다. 이 차이를 평가하기 위해 S6A required tool failure와 S6B optional tool failure를 분리했습니다.

### 7.6 LLM은 계약 안에서만 사용했다

LLM은 case parser, planner, checklist extractor, clarification, drafting에 사용할 수 있습니다.

하지만 LLM이 새로운 tool을 만들거나, allowed data_need 밖의 항목을 요청하거나, expected cause를 직접 출력하거나, 결제/환불/설정 변경을 제안하는 것은 금지했습니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 “매장 결제 장애를 LLM이 분류해주는 데모”처럼 보일 수 있습니다.

하지만 개발하면서 핵심은 LLM 자체가 아니라, **운영 데이터를 안전하게 조회하고 근거 기반으로 판단하는 workflow**라는 점이 분명해졌습니다.

첫 번째 전환점은 도메인 원인 분리였습니다. 같은 승인 실패라도 duplicate TID, 단말기 식별자 불일치, VAN 등록 미완료, POS-Front 연결 문제는 확인해야 할 데이터가 다릅니다. 그래서 case family별 golden set과 required tool set을 만들었습니다.

두 번째 전환점은 synthetic fixture 설계였습니다. raw DB에 정답 원인을 넣으면 agent가 실제 추론을 한 것이 아니라 정답을 읽은 것이 됩니다. 그래서 정답은 golden JSON에만 두고, SQLite에는 운영 fact만 넣었습니다.

세 번째 전환점은 safety gate였습니다. 결제 운영에서는 틀린 원인보다 위험한 것이 근거 없는 확신입니다. 그래서 supporting evidence 없는 likely claim을 실패로 보고, 도구 실패와 충돌 증거는 별도 상태로 라우팅했습니다.

네 번째 전환점은 LLM 평가였습니다. LLM smoke test에서 상태와 원인은 맞았지만 required tool 하나를 빠뜨렸습니다. 이 결과를 통해 LLM은 이해력은 좋지만 SOP coverage는 별도 guardrail과 evaluation이 필요하다는 점을 확인했습니다.

최종적으로 StoreOps Triage Agent는 “결제 장애 챗봇”이 아니라, **운영 정책, 읽기 전용 도구, evidence record, safety gate, evaluation이 결합된 결제 장애 조사 워크플로우**로 정리되었습니다.

---

## 9. Limitations

이 프로젝트는 합성 데이터 기반 포트폴리오 MVP이며, 실제 운영 시스템으로 확장하려면 추가 검증이 필요합니다.

첫째, 데이터는 synthetic 50-case fixture입니다. 실제 매장 운영 데이터에서는 네트워크 장애, 결제망 지연, 카드사 응답, 중복 증상, 부분 장애가 더 복잡하게 섞일 수 있습니다.

둘째, deterministic evaluation은 38/50 통과로 아직 개선 여지가 있습니다. 특히 모호 문의, required tool recall, optional tool failure, temporal conflict 처리에서 추가 보강이 필요합니다.

셋째, LLM smoke test는 1개 케이스 기준입니다. 실제 LLM 경로를 평가하려면 50개 전체 케이스에서 required tool recall, forbidden action safety, evidence citation coverage를 반복 측정해야 합니다.

넷째, 현재 tool gateway는 SQLite fixture 기반입니다. 실제 운영 환경에서는 로그 시스템, 단말기 관리 시스템, VAN 상태 조회, POS 연동 로그와의 connector가 필요합니다.

다섯째, 이 시스템은 조치 실행을 하지 않습니다. 실제 운영에서는 담당자 승인 후 설정 변경, 설치 대행 확인, VAN 문의, 고객 안내까지 연결되는 workflow가 필요합니다.

여섯째, 정책 문서는 synthetic SOP입니다. 실제 회사 적용 시에는 실제 운영 정책, 장애 대응 권한, 고객 안내 문구, 개인정보/보안 기준을 반영해야 합니다.

---

## 10. How to Run

### Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

또는 requirements 기반으로 실행합니다.

```powershell
pip install -r requirements.txt
```

### Run deterministic evaluation

프로젝트 루트에서 실행합니다.

```powershell
$env:PYTHONPATH = "src"
python -m storeops.evals.runner
```

예상 요약은 다음과 같습니다.

```json
{
  "total_cases": 50,
  "passed_cases": 38,
  "state_accuracy": 0.9,
  "cause_accuracy": 0.98,
  "abstention_safety_accuracy": 1.0,
  "unsupported_claim_count": 0
}
```

### Run live LLM smoke test

OpenAI-compatible API를 사용할 수 있습니다.

```powershell
$env:PYTHONPATH = "src"
$env:LIVE_LLM_API_KEY = "your_key"
$env:LIVE_LLM_BASE_URL = "https://api.deepseek.com"
$env:LIVE_LLM_MODEL = "deepseek-chat"
$env:LIVE_LLM_TIMEOUT_SECONDS = "20"

python -m storeops.evals.llm_runner `
  --provider live `
  --fixture-key SYN-001 `
  --output-dir experiments/eval_runs/llm/deepseek_smoke_SYN001
```

전체 50개 케이스를 실행하려면 `--fixture-key SYN-001`을 제거합니다.

### Run tests

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q -p no:cacheprovider
```

---

## 11. Project Structure

```text
storeops-triage-agent/
├── README.md
├── pyproject.toml
├── config/
├── data/
│   ├── fixtures/
│   │   ├── offline_payment_ops_synthetic_50.sqlite3
│   │   └── offline_payment_ops_synthetic_50_manifest.json
│   ├── golden/
│   │   └── offline_payment_ops_cases_50.json
│   ├── evaluation/
│   │   ├── planner_cases_50.json
│   │   └── retrieval_cases_50.json
│   ├── policies/
│   │   └── offline_payment_ops/
│   └── tool_catalog/
│       └── offline_payment_ops_tools.json
├── docs/
│   ├── architecture.md
│   ├── data-contract.md
│   └── evaluation.md
├── reports/
│   ├── synthetic_50_validation_report.md
│   └── synthetic_50_validation_matrix.csv
├── scripts/
│   └── generate_offline_payment_synthetic_50.py
├── src/
│   └── storeops/
│       ├── core/
│       ├── domains/
│       │   └── offline_payment_ops/
│       ├── evals/
│       ├── infra/
│       ├── llm/
│       └── observability/
├── tests/
└── experiments/
    ├── eval_runs/
    ├── legacy_code/
    ├── legacy_docs/
    └── legacy_s1_s7/
```

`experiments/`에는 이전 데모, legacy S1-S7 자산, 과거 출력물이 보존되어 있습니다. 제출/포트폴리오 기준 canonical runtime은 synthetic 50-case dataset과 `src/storeops/` 경로입니다.

---

## 12. What This Project Demonstrates

이 프로젝트는 LLM을 오프라인 결제 운영 장애 대응에 적용할 때 필요한 안전한 agent 설계를 보여줍니다.

첫째, 가맹점주의 짧은 문의를 결제 운영 사건으로 구조화하고, 원인 후보를 바로 단정하지 않는 workflow를 만들었습니다.

둘째, SOP/RAG와 tool catalog를 이용해 확인해야 할 data_need를 계획하고, 모든 운영 조회를 read-only tool로 제한했습니다.

셋째, raw SQLite fixture에는 정답을 넣지 않고 운영 fact만 넣어, agent가 실제 evidence를 조합해 원인을 판단하도록 설계했습니다.

넷째, duplicate TID, 단말기 식별자 불일치, VAN 등록 미완료, POS-Front 연결 장애, 모호 문의, 도구 실패, 시간축 충돌까지 포함한 50개 합성 평가셋을 만들었습니다.

다섯째, tool response를 바로 판단에 쓰지 않고 evidence record로 정규화해 supports/contradicts 관계를 남겼습니다.

여섯째, supporting evidence 없는 likely claim, 필수 도구 실패, 현장 설명과 시스템 기록 충돌을 safety gate에서 차단했습니다.

일곱째, deterministic 평가에서 state accuracy 0.90, cause accuracy 0.98, abstention safety accuracy 1.00, unsupported claim count 0을 기록했습니다.

여덟째, LLM을 도입하더라도 allowed data_need, tool catalog, prompt contract, safety gate 안에서만 작동하도록 제한했습니다.

이 프로젝트의 핵심은 단순히 결제 장애를 분류한 것이 아니라, **매장 운영 문의를 근거 조회, 안전 판단, 운영자 검토가 가능한 evidence-backed triage workflow로 바꾼 것**입니다.
