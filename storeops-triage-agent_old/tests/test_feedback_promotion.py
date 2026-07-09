import json
import tempfile
import unittest
from pathlib import Path

from storeops.feedback_loop.promotion import promote_feedback_candidate


class FeedbackPromotionTests(unittest.TestCase):
    def test_promotion_requires_explicit_approval(self):
        candidate = {
            "case_id": "CASE-S1",
            "final_cause": "duplicate_tid",
            "stage_summary": {"state": "READY_FOR_REVIEW"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            promoted_path = Path(tmpdir) / "promoted_cases.jsonl"
            with self.assertRaises(ValueError):
                promote_feedback_candidate(promoted_path, candidate, approved=False)

    def test_promotion_writes_promoted_jsonl_record(self):
        candidate = {
            "case_id": "CASE-S1",
            "final_cause": "duplicate_tid",
            "stage_summary": {"state": "READY_FOR_REVIEW"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            promoted_path = Path(tmpdir) / "promoted_cases.jsonl"
            promote_feedback_candidate(promoted_path, candidate, approved=True)
            payload = json.loads(promoted_path.read_text(encoding="utf-8").strip())

        self.assertTrue(payload["approved"])
        self.assertEqual(payload["case_id"], "CASE-S1")


if __name__ == "__main__":
    unittest.main()
