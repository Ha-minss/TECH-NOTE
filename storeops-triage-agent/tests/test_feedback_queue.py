import json
import tempfile
import unittest
from pathlib import Path

from storeops.feedback_loop.queue import enqueue_feedback_candidate
from storeops.operator.feedback import FeedbackRecord


class FeedbackQueueTests(unittest.TestCase):
    def test_feedback_queue_appends_jsonl_candidate(self):
        feedback = FeedbackRecord(
            case_id="CASE-S1",
            cause_verdict="incorrect",
            final_cause="terminal_identifier_mismatch",
            response_edited=True,
            edited_response="수정된 답변",
            reviewer_id="OP-DEMO",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "review_queue.jsonl"
            enqueue_feedback_candidate(queue_path, feedback, stage_summary={"state": "READY_FOR_REVIEW"})
            lines = queue_path.read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["case_id"], "CASE-S1")
        self.assertEqual(payload["stage_summary"]["state"], "READY_FOR_REVIEW")


if __name__ == "__main__":
    unittest.main()
