from __future__ import annotations

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def preprocess_model_matrix(frame: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare a clean feature matrix for modeling examples."""
    y = frame[target_col].astype(int)
    X = frame.drop(columns=[target_col])
    numeric_cols = X.select_dtypes(include="number").columns

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_numeric = pd.DataFrame(
        imputer.fit_transform(X[numeric_cols]),
        columns=numeric_cols,
        index=X.index,
    )
    X_numeric = pd.DataFrame(
        scaler.fit_transform(X_numeric),
        columns=numeric_cols,
        index=X.index,
    )
    return X_numeric, y
