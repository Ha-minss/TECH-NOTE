from __future__ import annotations

import pandas as pd


def calculate_normalized_net_benefit(policy_table: pd.DataFrame, ead: float, lgd: float, intervention_effect: float, review_cost: float, friction_cost: float) -> pd.DataFrame:
    """Calculate normalized cost-sensitive review policy value."""
    out = policy_table.copy()
    out["avoided_loss"] = out["tp"] * ead * lgd * intervention_effect
    out["review_cost_total"] = out["weighted_review_count"] * review_cost
    out["friction_cost_total"] = out["weighted_fp"] * friction_cost
    out["net_benefit"] = out["avoided_loss"] - out["review_cost_total"] - out["friction_cost_total"]
    out["net_benefit_per_review"] = out["net_benefit"] / out["weighted_review_count"]
    return out
