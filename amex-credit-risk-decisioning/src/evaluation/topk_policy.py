from __future__ import annotations

import math

import pandas as pd


def simulate_topk_policy(frame: pd.DataFrame, score_col: str, target_col: str, review_rates: list[float]) -> pd.DataFrame:
    """Evaluate manual-review policies at several Top-K review capacities."""
    ranked = frame.sort_values(score_col, ascending=False).reset_index(drop=True)
    total_defaults = ranked[target_col].sum()
    overall_default_rate = ranked[target_col].mean()
    rows = []
    for rate in review_rates:
        review_count = math.ceil(len(ranked) * rate)
        reviewed = ranked.head(review_count)
        tp = int(reviewed[target_col].sum())
        fp = int(review_count - tp)
        rows.append(
            {
                "policy": f"Top {int(rate * 100)}%",
                "review_rate": rate,
                "review_count": review_count,
                "tp": tp,
                "fp": fp,
                "precision": tp / review_count,
                "capture_rate": tp / total_defaults,
                "lift": (tp / review_count) / overall_default_rate,
            }
        )
    return pd.DataFrame(rows)
