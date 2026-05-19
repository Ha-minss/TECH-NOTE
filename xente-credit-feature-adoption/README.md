# Xente Credit Feature Adoption

상환 이력이 없는 고객의 신용위험 판단에서 대출 전 거래 행동 변수를 핵심 feature로 채택할 수 있는지 검증한 프로젝트입니다.

## Summary

- **Question:** 대출 전 거래 행동은 상환 이력이 없는 고객의 미상환 위험을 설명하는 독립적인 신호인가?
- **Finding:** 거래 이력 없음 그룹의 높은 미상환율은 리테일, 대출 공급자 2, 서비스 흐름 ID 6과 강하게 얽혀 있었습니다.
- **Decision:** 현재 데이터에서는 거래 행동 변수를 핵심 신용평가 변수로 바로 채택하기보다, 보조 관찰 변수로 두고 고위험 서비스 흐름을 우선 관리하는 판단이 더 적절합니다.

## Structure

```text
xente-credit-feature-adoption/
|-- README.md
|-- requirements.txt
|-- notebooks/
|   |-- 01_preprocessing.ipynb
|   |-- 02_eda_visualization.ipynb
|   |-- 03_modeling.ipynb
|   `-- 04_validation_interpretation.ipynb
|-- outputs/
|   |-- figures/
|   `-- tables/
`-- data/
    `-- README.md
```

## Notebook Flow

1. `01_preprocessing.ipynb`: raw data check and loan-level model table build
2. `02_eda_visualization.ipynb`: EDA and final visualization outputs
3. `03_modeling.ipynb`: baseline vs transaction-added model comparison
4. `04_validation_interpretation.ipynb`: score band, robustness, SHAP, and interpretation checks

## Run

```powershell
cd xente-credit-feature-adoption
python -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path .tmp\.jupyter-runtime | Out-Null
$env:TEMP=(Resolve-Path .tmp).Path
$env:TMP=(Resolve-Path .tmp).Path
$env:TMPDIR=(Resolve-Path .tmp).Path
$env:JUPYTER_RUNTIME_DIR=(Resolve-Path .tmp\.jupyter-runtime).Path
$env:JUPYTER_ALLOW_INSECURE_WRITES='1'

$notebooks = @(
  "notebooks/01_preprocessing.ipynb",
  "notebooks/03_modeling.ipynb",
  "notebooks/02_eda_visualization.ipynb",
  "notebooks/04_validation_interpretation.ipynb"
)

foreach ($nb in $notebooks) {
  python -m nbconvert --log-level ERROR --to notebook --execute $nb --inplace
}
```

Raw data is not tracked in this repository. See `data/README.md`.
