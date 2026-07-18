# Gamelytics A/B Analysis

모바일 게임 프로모션 A/B 테스트에서 관측 ARPU, 결제율, ARPPU, 매출 집중도, 그리고 ARPU 차이의 불확실성을 검증한 재현 가능한 분석 프로젝트입니다.

## 1. 문제 정의

B 그룹의 관측 ARPU는 A 그룹보다 높았지만 결제 전환율은 낮았습니다. 또한 A 그룹은 소수 고액 결제자에게 매출이 크게 집중되어, 단순 평균만으로 프로모션을 선택하기 어려웠습니다.

최종 의사결정 질문은 다음입니다.

> 현재 데이터만으로 B 프로모션을 전면 적용할 수 있는가, 아니면 추가 A/B 실험이 필요한가?

## 2. 데이터 감사 및 분석 범위

분석의 source of truth는 `ab_test.csv`입니다. `reg_data.csv`, `auth_data.csv`는 Retention 보조 분석에만 사용하며, `ab_test.user_id`와 `reg_data.uid`가 같은 identity namespace라고 주장하지 않습니다.

- A/B 사용자 수: A 202,103명, B 202,667명
- 결제자 수: A 1,928명, B 1,805명
- 중복 `user_id`: 0
- 결측값: 0
- 음수 revenue: 0
- CSV 구분자: 세미콜론(`;`)
- Sample Ratio Mismatch: chi-square 0.785869, p-value 0.375352

## 3. Primary / Secondary Metrics

Primary metric은 전체 배정 유저 기준 ARPU입니다.

```text
ARPU = total revenue / assigned users
```

Secondary metrics는 결제율, ARPPU, 결제자 수, 총매출, 매출 집중도입니다.

```text
ARPU = conversion rate x ARPPU
```

ARPPU는 결제자만을 조건으로 한 사후 지표이므로 독립적인 treatment effect처럼 해석하지 않습니다.

## 4. 핵심 결과

| Metric | A | B |
|---|---:|---:|
| Users | 202,103 | 202,667 |
| Payers | 1,928 | 1,805 |
| Conversion rate | 0.9540% | 0.8906% |
| Total revenue | 5,136,189 | 5,421,603 |
| ARPU | 25.4137 | 26.7513 |
| ARPPU | 2,664.00 | 3,003.66 |

B-A 결과:

- ARPU 차이: +1.3376
- 관측 ARPU lift: +5.2632%
- 결제율 차이: -0.0633%p
- ARPPU 차이: +339.66

## 5. 통계 검증

- 결제율 z-test p-value: 0.035029
- ARPU bootstrap 95% CI: -2.8733 ~ +5.4648
- ARPU permutation test p-value: 0.5272
- ARPPU bootstrap 95% CI: -69.43 ~ +732.98

Bootstrap은 95% confidence interval을 보기 위한 용도로 사용했고, permutation test는 ARPU 차이에 대한 p-value를 보기 위한 용도로 분리했습니다.

통계적으로 유의하지 않다는 것은 효과가 없다는 뜻이 아니라, 현재 데이터로 효과를 확정하기 어렵다는 뜻입니다.

## 6. Whale 민감도

Primary analysis는 원본 전체 유저 기준 결과입니다. Whale을 이상치라고 단정하거나 임의 삭제하지 않고, A 그룹이 소수 고액 결제자에게 얼마나 의존하는지와 그로 인해 평균의 불확실성이 커졌다는 점만 설명합니다.

최종 민감도 표는 다음 세 조건만 사용합니다.

| Scenario | A ARPU | B ARPU | B-A | 95% CI |
|---|---:|---:|---:|---:|
| 원본 전체 데이터 | 25.4137 | 26.7513 | +1.3376 | -2.8733 ~ +5.4648 |
| 공통 상위 0.1% winsorization | 4.9379 | 26.5236 | +21.5857 | +20.2830 ~ +22.9363 |
| 공통 상위 0.5% winsorization | 2.9359 | 3.4734 | +0.5375 | +0.3256 ~ +0.7520 |

A 그룹 매출 집중도:

- 상위 1% 결제자 매출 점유율: 13.82%
- 상위 5% 결제자 매출 점유율: 69.76%
- 상위 10% 결제자 매출 점유율: 89.90%

B 그룹 매출 집중도:

- 상위 1% 결제자 매출 점유율: 1.33%
- 상위 5% 결제자 매출 점유율: 6.56%
- 상위 10% 결제자 매출 점유율: 12.94%

## 7. 최종 의사결정

B의 관측 ARPU는 높았지만 ARPU 차이의 신뢰구간이 0을 포함했고, 결제 전환율은 유의하게 낮았습니다. 또한 A 그룹의 매출은 소수 고액 결제자에게 크게 집중되어 결과 변동성이 컸습니다.

따라서 현재 데이터만으로 B를 전면 적용하지 않고, 새로운 유저 표본으로 실제 서비스 A/B 테스트를 다시 진행하는 추가 실험을 권고합니다.

## 8. Portfolio PAAR

제목: **ARPU 상승과 결제율 하락이 충돌한 모바일 게임 프로모션 실험에서, 매출 불확실성을 검증해 출시 결정을 보류했습니다.**

Problem: B의 관측 ARPU는 A보다 높았지만 결제 전환율은 낮았습니다. 또한 A 그룹은 소수 고액 결제자에게 매출이 크게 집중되어, 단순 평균만으로 프로모션을 선택하기 어려웠습니다.

Analyze: ARPU를 결제율과 ARPPU로 분해하고, ARPU 차이가 실제 우위인지 아니면 heavy-tail 매출 변동으로 발생한 것인지 확인해야 한다고 판단했습니다. 특히 ARPPU는 결제자 조건부 지표이므로 primary metric인 전체 배정 유저 기준 ARPU와 분리해 해석했습니다.

Action: A/B 배정 품질을 검사하고, 결제율 z-test, 유저 단위 bootstrap, permutation test, 공통 기준 winsorization 민감도 분석을 수행했습니다. Whale을 임의 삭제하지 않고 원본 전체 유저 기준 결과를 primary analysis로 유지했습니다.

Result: B의 관측 ARPU는 5.26% 높았지만, B-A 차이의 95% CI는 -2.87~+5.46으로 0을 포함했습니다. 결제율은 0.0633%p 유의하게 낮아, B를 즉시 전면 적용하지 않고 추가 실험을 권고했습니다.

## 9. Supporting Analysis: Retention

Retention은 A/B 테스트 결론에 사용하지 않는 별도 보조 분석입니다. A/B user_id와 reg/auth uid가 동일한 identity namespace라고 주장하지 않으며, 두 분석을 유저 수준으로 조인하지 않습니다.

| Day | Eligible users | Retained users | Retention |
|---:|---:|---:|---:|
| D1 | 998,952 | 20,071 | 2.0092% |
| D2 | 997,311 | 40,997 | 4.1108% |
| D3 | 995,673 | 46,338 | 4.6539% |
| D7 | 989,145 | 58,140 | 5.8778% |
| D14 | 977,825 | 44,726 | 4.5740% |
| D30 | 952,434 | 26,971 | 2.8318% |

D0는 등록과 첫 auth 이벤트가 함께 기록된 것으로 보이므로 의사결정 해석에서 제외합니다.

## 10. Reproduce

원본 CSV는 저장소에 복사하지 않습니다. 데이터 경로를 인자로 전달합니다.

```powershell
& 'C:\Users\dongha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/run_ab_analysis.py --data-dir "C:\dev\Codex\gamelytics_data" --bootstrap-iterations 5000 --permutation-iterations 5000 --seed 42
& 'C:\Users\dongha\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/run_retention_analysis.py --data-dir "C:\dev\Codex\gamelytics_data"
python -m pytest tests -q
```

## 11. Generated Outputs

- `reports/data_audit.md`
- `reports/ab_analysis.md`
- `reports/ab_group_summary.csv`
- `reports/revenue_distribution_summary.csv`
- `reports/inference_summary.csv`
- `reports/whale_sensitivity_summary.csv`
- `reports/retention_analysis.md`
- `reports/retention_summary.csv`
- `reports/figures/ab_metric_comparison.png`
- `reports/figures/ab_metric_comparison.svg`
- `reports/figures/revenue_concentration.png`
- `reports/figures/revenue_concentration.svg`
- `reports/figures/arpu_bootstrap_distribution.png`
- `reports/figures/arpu_bootstrap_distribution.svg`
- `reports/figures/whale_sensitivity.png`
- `reports/figures/whale_sensitivity.svg`
- `reports/figures/monthly_retention_heatmap.png`
- `reports/figures/monthly_retention_heatmap.svg`

## 12. Limitations

- 프로모션 비용, 마진, 할인 정보가 없어 ROI가 아니라 gross revenue 기준으로 해석합니다.
- ARPU 차이의 신뢰구간이 0을 포함하므로 현재 데이터만으로 B의 안정적인 우위를 확인하지 못했습니다.
- Retention 분석은 A/B 실험 결론과 결합하지 않습니다.
