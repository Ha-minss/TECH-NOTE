import json
import unittest

from storeops.apps.operator_cli import run


class OperatorCliTests(unittest.TestCase):
    def test_operator_cli_json_returns_operator_view_model_shape(self):
        payload = run("S1")

        self.assertEqual(payload["case_id"], "CASE-S1")
        self.assertEqual(payload["state"], "READY_FOR_REVIEW")
        self.assertEqual(payload["primary_cause"], "duplicate_tid")
        self.assertEqual(
            [section["key"] for section in payload["sections"]],
            [
                "current_status",
                "cause_or_abstention",
                "next_action",
                "handoff_target",
                "merchant_response_draft",
                "evidence_summary",
                "technical_details",
            ],
        )
        json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
