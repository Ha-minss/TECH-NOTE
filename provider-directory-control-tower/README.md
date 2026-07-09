# Provider Directory Control Tower

의료 제공자(provider) 디렉터리의 기존 등록 정보를 NPI Registry와 CMS 공개 데이터로 검증하고, 변경 후보를 **자동 업데이트 / 사람 검토 / 직접 확인 요청 / 변경 없음**으로 라우팅하는 Provider Directory Validation 프로젝트입니다.

이 프로젝트의 핵심은 “provider 정보를 최신화한다”가 아닙니다. 의료 디렉터리 정보는 이름, NPI, 진료과, 주소, 전화번호, 활성 상태처럼 운영과 신뢰에 직접 연결되기 때문에, 단순 크롤링이나 LLM 판단으로 바로 수정하면 위험합니다.

Provider Directory Control Tower는 기존 provider record를 공식 출처 evidence와 대조하고, 필드별 변경 후보·신뢰도·근거 출처·감사 로그를 남긴 뒤, 안전한 정책에 따라 업데이트 가능 여부를 결정하는 **검증 워크플로우**입니다.

---

## 1. Overview

의료 provider directory는 환자, 보험사, 플랫폼, 병원 운영팀이 모두 의존하는 중요한 데이터입니다.

디렉터리에 잘못된 전화번호가 있으면 환자는 예약하지 못하고, 주소가 틀리면 방문 실패가 발생할 수 있습니다. 더 위험한 것은 provider의 active status, specialty, practice affiliation 같은 민감한 필드를 잘못 수정하는 경우입니다.

이 프로젝트는 HealthLynked 스타일의 provider/practice directory update 문제를 다음처럼 정의했습니다.

> 기존 provider record를 공식 출처와 대조해  
> 어떤 필드는 자동 업데이트하고, 어떤 필드는 사람 검토로 보내야 하는지 결정하자.

입력은 기존 provider directory record입니다.

```text
provider_id
provider_name
npi
specialty
practice_name
address
phone
website
last_verified_date
active_status
```

시스템은 각 record에 대해 NPI Registry와 CMS 공개 데이터에서 evidence를 수집하고, 값을 정규화한 뒤, 기존 값과 의미 있는 차이가 있는지 확인합니다.

최종 출력은 단순 수정값이 아니라 다음 정보를 포함하는 recommendation입니다.

```text
provider_id
npi
change_detected
field-level changes
old_value / new_value
confidence_score
supporting_sources
evidence_snippets
recommended_action
reason
audit_id
```

추천 action은 네 가지입니다.

| Action | 의미 |
|---|---|
| `no_change` | 공식 evidence와 비교했을 때 기존 record가 유지 가능 |
| `auto_update` | 낮은 위험 필드에서 충분한 근거와 신뢰도가 있어 자동 업데이트 가능 |
| `human_review` | 충돌, 고위험 필드, revoked/inactive 신호 등으로 사람 검토 필요 |
| `outreach_required` | evidence가 부족해 provider/practice에 직접 확인 필요 |

샘플 실행에서는 20개 provider record를 처리했고, 19건은 `no_change`, 1건은 `human_review`로 라우팅되었습니다.

핵심 결론은 다음과 같습니다.

> Provider directory 업데이트는 “값이 다르다”만으로 자동 수정하면 안 된다.  
> 출처 신뢰도, 출처 간 합의, NPI 기반 identity match, 정보 최신성, 필드 위험도를 함께 보고 action을 결정해야 한다.

---

## 2. Problem & Objective

Provider directory 업데이트는 겉으로 보면 단순한 데이터 정제 문제처럼 보입니다.

하지만 실제 운영에서는 훨씬 민감합니다. 같은 provider 이름이라도 동명이인이 있을 수 있고, 하나의 NPI가 여러 데이터셋에서 다르게 보일 수 있으며, CMS 데이터는 목적에 따라 “수정 근거”가 아니라 “검토 신호”로만 써야 하는 경우도 있습니다.

예를 들어 전화번호나 주소는 공식 NPI Registry에서 명확히 확인되면 자동 업데이트 후보가 될 수 있습니다. 반면 provider name, specialty, practice name, active status는 잘못 바꾸면 환자 안내, 보험 청구, 검색 노출, compliance에 영향을 줄 수 있으므로 사람 검토가 필요합니다.

이 프로젝트가 해결하려는 문제는 다음과 같습니다.

| 문제 | 왜 어려운가 | 이 프로젝트의 접근 |
|---|---|---|
| provider 정보가 오래될 수 있음 | 주소, 전화번호, 상태가 시간이 지나며 바뀜 | `last_verified_date`와 공식 evidence를 함께 확인 |
| 출처마다 값이 다를 수 있음 | NPI와 CMS 데이터가 같은 역할을 하지 않음 | source agreement와 conflict를 분리 |
| 고위험 필드를 잘못 바꾸면 위험함 | 이름, specialty, active status는 운영 영향이 큼 | high-risk field는 자동 업데이트 제한 |
| LLM/웹 검색 결과를 그대로 쓰기 어려움 | hallucination, 페이지 오류, 비공식 출처 문제 | 기본 경로는 NPI/CMS 구조화 evidence만 사용 |
| 업데이트 근거가 남아야 함 | 운영자가 왜 바뀌었는지 확인해야 함 | evidence packet과 audit log 생성 |
| 대량 record를 처리해야 함 | 수작업 검증만으로는 확장 어려움 | batch pipeline과 recommendation output 생성 |

따라서 이 프로젝트의 목표는 세 가지입니다.

첫째, provider record를 공식 출처 evidence와 대조합니다.

둘째, 필드별 변경 후보를 만들고 confidence를 계산합니다.

셋째, 안전 정책에 따라 `no_change`, `auto_update`, `human_review`, `outreach_required`로 라우팅합니다.

---

## 3. Data

입력 데이터는 provider directory의 기존 record입니다.

샘플 입력은 `data/input/provider_records.jsonl`에 JSONL 형태로 저장되어 있습니다.

각 record는 다음 정보를 포함합니다.

| 필드 | 의미 | 사용 목적 |
|---|---|---|
| `provider_id` | 내부 provider 식별자 | audit, recommendation 연결 |
| `provider_name` | provider 이름 | 공식 출처와 identity 확인 |
| `npi` | National Provider Identifier | 핵심 identity anchor |
| `specialty` | 주 진료과/전문분야 | NPI taxonomy, CMS provider type과 비교 |
| `practice_name` | practice 또는 organization 이름 | affiliation/practice 검토 |
| `address` | practice location 주소 | NPI location address와 비교 |
| `phone` | practice location 전화번호 | NPI location phone과 비교 |
| `website` | provider/practice website | 낮은 위험 업데이트 후보 |
| `last_verified_date` | 마지막 검증일 | recency score 계산 |
| `active_status` | active/inactive 등 상태 | NPI status, CMS revoked signal과 비교 |

샘플 record는 다음과 같은 형태입니다.

```json
{
  "provider_id": "NPI1_00001",
  "provider_name": "AMBAR M ABADI ALVAREZ",
  "npi": "1598284069",
  "specialty": "Behavior Technician",
  "practice_name": "",
  "address": "8275 IBIS CLUB DR APT 702, NAPLES, FL, 341042416",
  "phone": "305-303-5351",
  "website": "",
  "last_verified_date": "2022-07-21",
  "active_status": "active"
}
```

사용한 evidence source는 크게 두 가지입니다.

| Evidence Source | 역할 |
|---|---|
| NPI Registry | NPI 유효성, active status, provider name, taxonomy, practice location address, phone 확인 |
| CMS Public Data | Medicare enrollment, provider type, state, revoked provider/supplier signal 확인 |

NPI Registry는 provider identity의 가장 중요한 anchor로 사용했습니다. NPI checksum과 Registry 조회 결과가 맞으면, 해당 record가 어떤 provider를 가리키는지 확인하는 강한 근거가 됩니다.

CMS 데이터는 목적별로 다르게 사용했습니다. Medicare FFS 데이터의 provider name과 specialty는 자동 수정 근거라기보다 확인용 context로 사용했고, CMS Revoked Medicare Providers and Suppliers 데이터는 강한 사람 검토 신호로 사용했습니다.

---

## 4. Method / System Design

이 프로젝트의 설계는 다음 원칙에서 출발합니다.

> 모든 evidence를 같은 무게로 보지 않는다.  
> 모든 필드를 같은 위험도로 보지 않는다.  
> 모든 변경을 자동으로 적용하지 않는다.

전체 흐름은 다음과 같습니다.

```text
Existing Provider Records
        ↓
Load JSONL Input
        ↓
Evidence Collection
(NPI Registry / CMS Public Data)
        ↓
Normalize Values
        ↓
Compare Current Record vs Evidence
        ↓
Generate Field-level Change Candidates
        ↓
Confidence Scoring
(source reliability / agreement / entity match / recency / field safety)
        ↓
Deterministic Decision Policy
        ↓
no_change / auto_update / human_review / outreach_required
        ↓
Recommendations / Evidence Packets / Audit Logs / Connector Diagnostics
```

### 4.1 Evidence collection

각 provider record에 대해 NPI를 기준으로 공식 출처를 조회합니다.

NPI Registry에서는 다음 evidence를 수집합니다.

| Evidence | 예시 |
|---|---|
| NPI validation | NPI format, checksum, Registry record 존재 여부 |
| Active status | active/inactive |
| Provider name | basic provider name |
| Specialty | primary taxonomy |
| Address | practice location address |
| Phone | practice location phone |

CMS에서는 설정한 source mode에 따라 Medicare FFS, revoked provider/supplier, facility-oriented datasets를 조회합니다.

기본 운영 모드는 `minimal`입니다.

| CMS mode | 의미 |
|---|---|
| `minimal` | Medicare FFS + Revoked checks. 기본 운영 경로 |
| `ffs` | Medicare FFS only |
| `revoked` | revoked provider/supplier checks only |
| `facility` | facility-oriented CMS datasets + revoked checks |
| `all` | whitelisted CMS datasets를 더 넓게 조회하는 조사 모드 |

### 4.2 Normalization

provider directory 데이터는 같은 값도 여러 형식으로 나타날 수 있습니다.

예를 들어 전화번호는 다음처럼 다르게 표시될 수 있습니다.

```text
305-303-5351
(305) 303-5351
3053035351
```

이 값들은 사람이 보기에는 같지만 문자열 비교로는 다릅니다. 따라서 필드별 normalization을 먼저 수행한 뒤 비교합니다.

| 필드 | 정규화 관점 |
|---|---|
| `npi` | 숫자만 추출, 10자리 형식, checksum 확인 |
| `phone` | 숫자 기반 비교, 표시용 format 분리 |
| `address` | 대소문자, 공백, 쉼표 등 표기 차이 완화 |
| `provider_name` | 대소문자와 credential 표기 차이 완화 |
| `active_status` | active / inactive / revoked / unknown vocabulary로 매핑 |

### 4.3 Confidence scoring

변경 후보가 생기면 단순히 “출처가 하나 있다”로 판단하지 않고, 다섯 가지 요소를 합쳐 confidence를 계산합니다.

```text
confidence =
  0.35 × source reliability
+ 0.25 × source agreement
+ 0.20 × entity match
+ 0.10 × recency
+ 0.10 × field safety
```

각 요소의 의미는 다음과 같습니다.

| 요소 | 의미 |
|---|---|
| Source reliability | NPI Registry, CMS Revoked 등 출처 자체의 신뢰도 |
| Source agreement | 같은 필드에 대해 출처들이 같은 값을 말하는지 |
| Entity match | evidence가 현재 record의 NPI와 같은 provider를 가리키는지 |
| Recency | 기존 record가 얼마나 오래 전에 검증되었는지 |
| Field safety | 해당 필드를 자동 변경해도 되는 위험도 |

중요한 점은 confidence가 높다고 해서 항상 자동 업데이트되는 것은 아니라는 점입니다.

high-risk field는 confidence가 높아도 사람 검토가 필요할 수 있습니다.

### 4.4 Decision policy

최종 action은 deterministic policy로 결정합니다.

| 조건 | Action |
|---|---|
| 변경 후보가 없음 | `no_change` |
| 낮은 위험 필드이고, confidence가 기준 이상이며, conflict가 없음 | `auto_update` |
| 출처 충돌이 있음 | `human_review` |
| high-risk field 변경 후보가 있음 | `human_review` |
| revoked/inactive 신호가 있음 | `human_review` |
| evidence가 부족하거나 직접 확인이 필요함 | `outreach_required` |

기본 설정은 다음과 같습니다.

| 설정 | 값 |
|---|---:|
| Auto-update threshold | 0.86 |
| Human-review threshold | 0.60 |
| Auto-update allowed fields | address, phone, website |
| High-risk fields | active_status, practice_name, provider_name, specialty |
| Stale after days | 365 |

이 정책 때문에 시스템은 보수적으로 동작합니다. 특히 active status, provider name, specialty 같은 필드는 잘못 바꾸면 운영 리스크가 크기 때문에 자동 업데이트하지 않고 사람 검토로 보냅니다.

---

## 5. Implementation

구현은 provider record를 읽고, evidence를 수집하고, recommendation을 생성하는 batch pipeline으로 구성했습니다.

주요 모듈은 다음과 같습니다.

| 모듈 | 역할 | 쉽게 말하면 |
|---|---|---|
| `run_pipeline.py` | CLI entrypoint | 전체 파이프라인 실행 |
| `repository.py` | JSONL repository | 기존 provider record 읽기/쓰기 |
| `npi.py` | NPI 유효성·NPI Registry helper | NPI 조회와 checksum 검증 |
| `sources.py` | NPI Registry client | 공식 NPI evidence 수집 |
| `cms.py` | CMS public data connector | CMS FFS/Revoked/facility evidence 수집 |
| `normalize.py` | 필드별 정규화 | 전화번호, 주소, 이름, 상태 비교 준비 |
| `confidence.py` | confidence 계산 | 출처 신뢰도와 합의도 점수화 |
| `decision.py` | 변경 후보와 action 결정 | auto_update/human_review 라우팅 |
| `report.py` | 결과 export | recommendation, audit, summary 저장 |
| `scripts/evaluate_pipeline.py` | explicit-input 평가 | ground truth가 있을 때 action 비교 |

출력물은 다음과 같습니다.

| 출력 파일 | 내용 |
|---|---|
| `recommendations.jsonl` | record별 recommendation |
| `recommendations_pretty.json` | 사람이 읽기 쉬운 recommendation |
| `submission.csv` | 제출/검토용 요약 CSV |
| `evidence_packets.jsonl` | 수집된 field-level evidence |
| `audit_log.jsonl` | record별 처리 단계와 결정 로그 |
| `connector_diagnostics.csv` | NPI/CMS connector 성공/실패/row count |
| `executive_summary.md` | 실행 결과 요약 |

이 프로젝트에서 의도적으로 제외한 것도 있습니다.

| 제외한 것 | 이유 |
|---|---|
| 검색엔진 기반 웹 크롤링 | 비공식 출처와 불안정한 페이지 품질 문제 |
| LLM 최종 판단 | hallucination과 책임성 문제 |
| UI 중심 demo wrapper | 제출용 MVP에서는 운영 pipeline이 핵심 |
| fixture demo source 의존 | 실제 공식 source 기반 경로를 기본으로 유지 |

---

## 6. Evaluation

샘플 실행은 `sample_outputs/live_run`에 저장된 결과를 기준으로 정리했습니다.

### 6.1 Run Summary

| 항목 | 결과 |
|---|---:|
| 처리한 provider records | 20 |
| `no_change` | 19 |
| `human_review` | 1 |
| `auto_update` | 0 |
| `outreach_required` | 0 |

샘플 실행에서 대부분의 record는 NPI Registry와 CMS evidence로 기존 정보가 확인되어 `no_change`로 분류되었습니다.

1건은 CMS Revoked Medicare Providers and Suppliers에서 revoked signal이 발견되어 `human_review`로 라우팅되었습니다.

### 6.2 Evidence Summary

| Evidence source | Evidence count |
|---|---:|
| NPI Registry | 120 |
| CMS Medicare FFS Public Provider Enrollment | 32 |
| CMS Revoked Medicare Providers and Suppliers | 2 |

필드별 evidence는 다음과 같이 수집되었습니다.

| Field | Evidence count |
|---|---:|
| `npi` | 29 |
| `provider_name` | 28 |
| `specialty` | 28 |
| `active_status` | 21 |
| `address` | 20 |
| `phone` | 20 |
| `cms_enrollment_state` | 8 |

Connector diagnostics 기준으로 NPI Registry lookup 20건과 CMS lookup 20건이 모두 `ok` 상태로 수행되었습니다.

CMS lookup에서는 9건이 CMS row/evidence를 찾았고, 11건은 whitelist dataset 안에서 해당 NPI row가 발견되지 않았습니다. 이 경우도 실패가 아니라 “CMS whitelist에서 추가 evidence 없음”으로 기록했습니다.

### 6.3 Human Review Case

샘플 실행에서 `human_review`로 분류된 케이스는 `NPI1_00015`입니다.

| 항목 | 값 |
|---|---|
| Provider ID | `NPI1_00015` |
| NPI | `1386606325` |
| 변경 후보 필드 | `active_status` |
| 기존 값 | `active` |
| 새 evidence 값 | `revoked` |
| Supporting source | CMS Revoked Medicare Providers and Suppliers |
| Confidence | 0.704 |
| Recommended action | `human_review` |
| Reason | Conflicting sources found. Manual verification recommended. |

이 케이스가 자동 업데이트되지 않은 이유는 명확합니다.

`active_status`는 high-risk field이고, revoked signal은 provider directory에서 매우 민감한 상태 변경입니다. 따라서 evidence가 있더라도 자동으로 active status를 바꾸지 않고, 담당자가 source를 확인하도록 `human_review`로 보냈습니다.

이 결과는 시스템의 보수적 정책을 보여줍니다.

> 낮은 위험 필드의 명확한 변경은 자동화 후보가 될 수 있지만,  
> provider 상태나 전문분야처럼 위험한 변경은 사람 검토를 거쳐야 한다.

### 6.4 Output Quality

이 프로젝트에서 중요한 출력 품질은 “몇 개를 업데이트했는가”가 아니라, 각 action에 대해 근거와 감사 가능성이 남는가입니다.

| 출력 품질 기준 | 결과 |
|---|---|
| Field-level old/new value 제공 | 변경 후보에 대해 제공 |
| Supporting source 제공 | field change마다 source list 제공 |
| Evidence snippet 제공 | CMS revoked reason 등 포함 |
| Confidence score 제공 | field-level 및 overall confidence 제공 |
| Audit ID 제공 | recommendation마다 audit_id 생성 |
| Connector diagnostics 제공 | NPI/CMS 조회 상태, row count, reason 기록 |
| Human review reason 제공 | conflict/high-risk/revoked 등 이유 기록 |

따라서 이 MVP는 자동 업데이트 수를 늘리는 데 초점을 둔 것이 아니라, provider directory 운영자가 안전하게 검토할 수 있는 recommendation package를 만드는 데 초점을 둡니다.

---

## 7. Key Design Decisions

### 7.1 LLM보다 공식 source evidence를 기본 경로로 사용했다

Provider directory는 의료 정보와 연결되기 때문에 비공식 웹 검색이나 LLM 생성값을 바로 업데이트 근거로 쓰면 위험합니다.

그래서 기본 경로는 NPI Registry와 CMS public data 같은 구조화된 공식 출처로 제한했습니다. LLM은 향후 비정형 웹 evidence 추출에 보조적으로 쓸 수 있지만, 최종 decision은 deterministic policy가 담당해야 합니다.

### 7.2 NPI를 identity anchor로 사용했다

provider name은 동명이인과 credential 표기 차이가 있을 수 있습니다. 주소나 전화번호도 시간이 지나며 바뀔 수 있습니다.

반면 NPI는 provider identity를 확인하는 가장 중요한 anchor입니다. 따라서 NPI format, checksum, NPI Registry record 존재 여부를 먼저 확인하고, 이후 name, specialty, address, phone evidence를 해석했습니다.

### 7.3 같은 evidence라도 필드에 따라 다르게 취급했다

전화번호와 주소는 상대적으로 자동 업데이트하기 쉬운 필드입니다. 반면 active status, provider name, specialty, practice name은 잘못 바꾸면 영향이 큽니다.

그래서 field safety를 따로 두고, auto-update allowed field를 address, phone, website로 제한했습니다.

### 7.4 CMS evidence는 자동 수정 근거와 검토 신호를 구분했다

CMS Medicare FFS 데이터는 provider name이나 specialty를 확인하는 context로 유용하지만, 이를 곧바로 directory의 이름·전문분야 자동 수정 근거로 쓰는 것은 위험합니다.

반면 CMS Revoked dataset은 강한 위험 신호입니다. revoked signal이 있으면 자동 수정이 아니라 human review로 보냅니다.

### 7.5 Confidence는 단일 점수가 아니라 여러 요소를 합성했다

출처가 믿을 만하다는 이유만으로 충분하지 않습니다. 같은 필드에 대해 다른 출처가 같은 값을 말하는지, NPI가 같은 provider를 가리키는지, 기존 record가 오래되었는지, 필드 자체가 안전한지도 봐야 합니다.

그래서 source reliability, source agreement, entity match, recency, field safety를 합쳐 confidence를 계산했습니다.

### 7.6 변경이 없다는 결과도 중요한 output으로 남겼다

Provider directory 운영에서는 “바꿀 것 없음”도 중요한 판단입니다.

NPI Registry와 CMS evidence로 현재 record가 확인되면 `no_change` recommendation을 남기고, audit log에 어떤 source를 조회했는지 기록했습니다. 이렇게 해야 나중에 “왜 업데이트하지 않았는가”도 설명할 수 있습니다.

---

## 8. Development Notes

이 프로젝트는 처음에는 provider 정보를 여러 출처에서 찾아 업데이트하는 문제처럼 보였습니다.

하지만 개발하면서 핵심은 “더 많은 출처를 긁어오는 것”이 아니라, **출처별 역할과 필드별 위험도를 분리하는 것**이라는 점이 분명해졌습니다.

첫 번째 전환점은 source selection이었습니다. 웹 검색이나 practice website scraping을 무작정 붙이면 많은 후보값을 얻을 수 있지만, 그 값이 현재 provider와 정확히 연결되는지 확인하기 어렵습니다. 그래서 최종 제출 경로에서는 NPI Registry와 CMS public data 중심으로 좁혔습니다.

두 번째 전환점은 CMS 데이터 해석이었습니다. CMS dataset은 모두 같은 목적이 아닙니다. 어떤 데이터는 provider type 확인에 좋고, 어떤 데이터는 facility/location evidence에 적합하며, revoked dataset은 상태 위험 신호입니다. 그래서 CMS connector를 whitelist 기반으로 만들고, dataset별 role을 명시했습니다.

세 번째 전환점은 auto-update 정책이었습니다. 처음에는 confidence가 높으면 자동 업데이트할 수 있을 것처럼 보이지만, active status나 specialty는 값이 맞아 보여도 담당자 확인이 필요합니다. 그래서 auto-update allowed fields를 address, phone, website로 제한했습니다.

네 번째 전환점은 auditability였습니다. 운영자는 recommendation만 보고 끝낼 수 없습니다. 어떤 source를 조회했고, 어떤 값이 나왔고, 왜 update가 아니라 review인지 확인할 수 있어야 합니다. 그래서 evidence packet, audit log, connector diagnostics를 모두 output으로 남겼습니다.

결과적으로 이 프로젝트는 “provider 정보를 맞추는 스크립트”가 아니라, **provider directory 운영자가 안전하게 업데이트 후보를 검토할 수 있는 control tower**로 정리되었습니다.

---

## 9. Limitations

이 프로젝트는 provider directory validation MVP이며, 실제 운영 시스템으로 확장하려면 추가 작업이 필요합니다.

첫째, 샘플 실행은 20개 provider record 기준입니다. 더 큰 규모의 provider directory에서 rate limit, retry, caching, batch scheduling을 추가로 검증해야 합니다.

둘째, NPI Registry와 CMS public data는 강한 공식 evidence이지만, provider website나 state medical board 같은 추가 출처가 필요한 케이스도 있습니다.

셋째, practice affiliation, website, provider availability 같은 정보는 NPI/CMS만으로 충분히 확인하기 어렵습니다. 이 경우 outreach workflow가 필요합니다.

넷째, CMS dataset은 목적과 업데이트 주기가 다르므로, 모든 CMS row를 동일한 수정 근거로 사용할 수 없습니다. dataset별 역할 정의와 monitoring이 필요합니다.

다섯째, confidence score는 운영 의사결정을 보조하는 점수이며, 실제 업데이트 승인 기준은 조직의 compliance policy에 맞게 조정해야 합니다.

여섯째, 이 MVP는 recommendation을 생성하지만 실제 production database를 직접 수정하지 않습니다. 운영 환경에서는 staging tables, approval workflow, rollback, monitoring이 필요합니다.

---

## 10. How to Run

### Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run the main pipeline

NPI Registry와 CMS public data를 사용하는 기본 실행 경로입니다.

```powershell
python run_pipeline.py `
  --input data\input\provider_records.jsonl `
  --use-real-npi `
  --use-cms `
  --cms-source minimal `
  --output-dir outputs\live_run
```

### CMS source modes

```text
minimal   Medicare FFS + Revoked checks
ffs       Medicare FFS only
revoked   Revoked provider/supplier checks only
facility  Facility-oriented CMS datasets + Revoked checks
all       Broader CMS sweep for small investigation runs
```

### Output files

```text
outputs/live_run/
├── executive_summary.md
├── submission.csv
├── recommendations.jsonl
├── recommendations_pretty.json
├── evidence_packets.jsonl
├── audit_log.jsonl
├── connector_diagnostics.csv
└── connector_diagnostics.json
```

### Evaluation utility

Ground truth label 파일이 있는 경우 action-level 평가를 실행할 수 있습니다.

```powershell
python scripts/evaluate_pipeline.py `
  --predictions outputs\live_run\recommendations.jsonl `
  --ground-truth data\ground_truth\labels.jsonl `
  --out-dir outputs\evaluation
```

---

## 11. Project Structure

```text
provider-directory-control-tower/
├── README.md
├── requirements.txt
├── run_pipeline.py
├── configs/
│   └── pipeline_config.json
├── data/
│   └── input/
│       └── provider_records.jsonl
├── outputs/
│   └── .gitkeep
├── sample_outputs/
│   └── live_run/
│       ├── audit_log.jsonl
│       ├── connector_diagnostics.csv
│       ├── connector_diagnostics.json
│       ├── evidence_packets.jsonl
│       ├── executive_summary.md
│       ├── recommendations.jsonl
│       ├── recommendations_pretty.json
│       └── submission.csv
├── scripts/
│   └── evaluate_pipeline.py
└── src/
    ├── cms.py
    ├── confidence.py
    ├── decision.py
    ├── models.py
    ├── normalize.py
    ├── npi.py
    ├── pipeline.py
    ├── report.py
    ├── repository.py
    ├── sources.py
    └── utils.py
```

---

## 12. What This Project Demonstrates

이 프로젝트는 의료 provider directory 업데이트를 단순 데이터 정제가 아니라, 안전한 운영 의사결정 문제로 다룹니다.

첫째, 기존 provider record를 NPI Registry와 CMS public data 같은 공식 source evidence로 검증했습니다.

둘째, NPI checksum과 Registry lookup을 통해 provider identity를 먼저 고정하고, 이후 name, specialty, address, phone, active status를 비교했습니다.

셋째, provider field를 모두 같은 위험도로 보지 않고, address/phone/website와 active_status/provider_name/specialty/practice_name을 다르게 취급했습니다.

넷째, source reliability, source agreement, entity match, recency, field safety를 결합해 field-level confidence를 계산했습니다.

다섯째, confidence가 높아도 high-risk field나 revoked signal은 자동 업데이트하지 않고 human review로 보냈습니다.

여섯째, recommendation, evidence packet, audit log, connector diagnostics를 함께 생성해 운영자가 왜 해당 action이 나왔는지 추적할 수 있게 했습니다.

일곱째, 샘플 실행에서 20개 provider record를 처리하고, 19건은 `no_change`, 1건은 CMS revoked signal로 `human_review`에 라우팅했습니다.

마지막으로, 실제 production에서는 기존 directory DB를 읽기 전용으로 연결하고, 결과를 `update_candidates`, `review_queue`, `outreach_queue`, `audit_log` 같은 staging table에 저장하는 구조로 확장할 수 있습니다.

이 프로젝트의 핵심은 단순히 provider 정보를 업데이트한 것이 아니라, **공식 evidence와 deterministic policy를 이용해 의료 디렉터리 변경을 안전하게 검토 가능한 recommendation workflow로 바꾼 것**입니다.
