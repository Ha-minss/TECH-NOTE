"""Append operator feedback to a review queue."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path


def enqueue_feedback_candidate(queue_path: Path | str, feedback, *, stage_summary: dict) -> dict:
    payload = asdict(feedback)
    payload["checklist_feedback"] = feedback.checklist_feedback
    payload["is_candidate_for_review_queue"] = feedback.is_candidate_for_review_queue
    payload["stage_summary"] = stage_summary
    payload["queued_at"] = datetime.now().isoformat()
    path = Path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


__all__ = ["enqueue_feedback_candidate"]
