from __future__ import annotations

import numpy as np
import pandas as pd


def clip_outliers_iqr(frame: pd.DataFrame, columns: list[str], multiplier: float = 1.5) -> pd.DataFrame:
    """Clip extreme values with the IQR rule for stable tabular modeling."""
    out = frame.copy()
    for col in columns:
        q1 = out[col].quantile(0.25)
        q3 = out[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        out[col] = out[col].clip(lower, upper)
    return out


def add_missing_indicators(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Add binary missing-value flags before imputation."""
    out = frame.copy()
    for col in columns:
        out[f"{col}_missing"] = out[col].isna().astype(np.int8)
    return out


def aggregate_customer_month_features(frame: pd.DataFrame, customer_col: str, numeric_cols: list[str]) -> pd.DataFrame:
    """Create customer-level summary features from customer-month observations."""
    aggregations = {col: ["mean", "std", "min", "max", "last"] for col in numeric_cols}
    customer_features = frame.groupby(customer_col).agg(aggregations)
    customer_features.columns = ["_".join(col).strip() for col in customer_features.columns]
    return customer_features.reset_index()
