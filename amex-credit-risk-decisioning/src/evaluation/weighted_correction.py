from __future__ import annotations

import pandas as pd


def apply_nondefault_weight(policy_table: pd.DataFrame, nondefault_weight: int = 20) -> pd.DataFrame:
    """Approximate broader population workload after AMEX non-default downsampling."""
    out = policy_table.copy()
    out["weighted_fp"] = out["fp"] * nondefault_weight
    out["weighted_review_count"] = out["tp"] + out["weighted_fp"]
    out["weighted_precision"] = out["tp"] / out["weighted_review_count"]
    return out
