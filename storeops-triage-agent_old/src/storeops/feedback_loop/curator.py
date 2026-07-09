"""Read queued feedback candidates for manual review."""

from __future__ import annotations

import json
from pathlib import Path


def load_review_queue(queue_path: Path | str) -> list[dict]:
    path = Path(queue_path)
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


__all__ = ["load_review_queue"]
