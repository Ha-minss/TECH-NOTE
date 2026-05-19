from __future__ import annotations

import pandas as pd


def build_risk_deciles(frame: pd.DataFrame, score_col: str, target_col: str) -> pd.DataFrame:
    """Summarize observed default concentration by score decile."""
    ranked = frame.sort_values(score_col, ascending=False).reset_index(drop=True)
    ranked["risk_decile"] = ((ranked.index / len(ranked)) * 10).astype(int) + 1
    ranked["risk_decile"] = ranked["risk_decile"].clip(upper=10)
    summary = (
        ranked.groupby("risk_decile", as_index=False)
        .agg(customers=(score_col, "count"), observed_defaults=(target_col, "sum"), avg_score=(score_col, "mean"))
    )
    summary["observed_default_rate"] = summary["observed_defaults"] / summary["customers"]
    return summary
