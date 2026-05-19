# Policy-Driven Revenue Persistence

소비 지원 정책 이후 서비스업 매출 상승이 지속 수요인지, 외부 정책 충격에 민감한 일시적 반응인지 검증한 포트폴리오 노트북입니다.

## Question

정책으로 오른 매출을 핀테크 가맹점 신용평가에서 상환 여력으로 바로 볼 수 있는가?

## Notebook Flow

| Notebook | Role |
|---|---|
| `01_data_preparation.ipynb` | 월별 분석 패널, 정책 강도, 분석 가능 범위 정리 |
| `02_eda_visualization.ipynb` | AFS 부문과 저노출 비교 부문의 흐름 및 2025년 정책 블록 확인 |
| `03_modeling_event_study.ipynb` | distributed lag, end-centered event study, stacked event study |
| `04_validation_interpretation.ipynb` | placebo, permutation, robustness, 신용평가 해석 |

## Main Result

공개 집계자료에서는 레스토랑 단독 장기 시계열을 확보하지 못해 최종 estimand를 accommodation-and-food-service relative response로 조정했습니다. 정책 이후 상대 반응과 일부 지속성은 관찰되지만, 이를 순수 정책효과나 직접적인 상환능력으로 해석하지 않습니다.

## Run

```powershell
python -m pip install -r requirements.txt
python -m nbconvert --to notebook --execute notebooks/01_data_preparation.ipynb --inplace
python -m nbconvert --to notebook --execute notebooks/02_eda_visualization.ipynb --inplace
python -m nbconvert --to notebook --execute notebooks/03_modeling_event_study.ipynb --inplace
python -m nbconvert --to notebook --execute notebooks/04_validation_interpretation.ipynb --inplace
```

Raw official downloads are excluded from this repository. The included CSV files are derived public-data panels and model outputs used by the notebooks.
