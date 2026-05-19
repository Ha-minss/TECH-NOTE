from __future__ import annotations

import pandas as pd


def predict_risk_scores(model, X: pd.DataFrame) -> pd.Series:
    """Return ranking-oriented risk scores from a fitted binary classifier."""
    return pd.Series(model.predict_proba(X)[:, 1], index=X.index, name="risk_score")
