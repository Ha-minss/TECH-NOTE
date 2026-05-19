from __future__ import annotations

import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def evaluate_ranking_score(y_true: pd.Series, score: pd.Series) -> dict[str, float]:
    """Evaluate score quality as a ranking problem."""
    return {
        "roc_auc": roc_auc_score(y_true, score),
        "average_precision": average_precision_score(y_true, score),
    }


def rank_scores(frame: pd.DataFrame, score_col: str) -> pd.DataFrame:
    """Sort customers from highest to lowest review priority."""
    out = frame.sort_values(score_col, ascending=False).reset_index(drop=True)
    out["risk_rank"] = out.index + 1
    out["risk_percentile"] = out["risk_rank"] / len(out)
    return out
