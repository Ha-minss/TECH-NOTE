"""Manual promotion of feedback into promoted Golden-case records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def promote_feedback_candidate(
    promoted_path: Path | str,
    candidate: dict,
    *,
    approved: bool,
) -> dict:
    if not approved:
        raise ValueError("Promotion requires explicit approval.")
    payload = {
        **candidate,
        "approved": True,
        "promoted_at": datetime.now().isoformat(),
    }
    path = Path(promoted_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


__all__ = ["promote_feedback_candidate"]
