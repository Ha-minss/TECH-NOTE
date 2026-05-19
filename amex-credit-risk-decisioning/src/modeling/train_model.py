from __future__ import annotations

from sklearn.linear_model import LogisticRegression


def train_baseline_model(X, y) -> LogisticRegression:
    """Train a lightweight baseline model for portfolio illustration."""
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X, y)
    return model
