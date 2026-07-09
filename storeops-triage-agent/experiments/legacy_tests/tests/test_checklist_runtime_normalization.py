import unittest

from storeops.llm.runtime import _normalize_checklist_output


class ChecklistRuntimeNormalizationTests(unittest.TestCase):
    def test_normalizes_single_policy_check_object_into_schema_envelope(self):
        raw = {
            "policy_id": "SOP-PAY-OP-003",
            "policy_title": "[운영표준] 가맹점/VAN 등록 상태 점검 지침",
            "check_text": "내부 운영 시스템에서 VAN 가맹점 등록 상태 확인",
            "matched_data_need": "van_registration_status",
            "priority": "required",
            "reason": "SOP requires checking registration status.",
            "source_quote": "VAN 가맹점 등록 상태",
        }

        normalized = _normalize_checklist_output("checklist_extractor", raw)

        self.assertEqual(normalized["confidence"], 0.8)
        self.assertEqual(len(normalized["policy_checks"]), 1)
        self.assertEqual(normalized["policy_checks"][0]["policy_id"], "SOP-PAY-OP-003")
        self.assertEqual(
            normalized["policy_checks"][0]["matched_data_need"],
            "van_registration_status",
        )

    def test_preserves_valid_policy_checks_list_and_adds_confidence(self):
        raw = {
            "policy_checks": [
                {
                    "policy_id": "SOP-PAY-OP-002",
                    "policy_title": "Terminal checks",
                    "check_text": "Check payment identifier config",
                    "matched_data_need": "payment_identifier_config",
                    "priority": "required",
                    "reason": "Required by SOP.",
                    "source_quote": "payment identifier config",
                }
            ]
        }

        normalized = _normalize_checklist_output("checklist_extractor", raw)

        self.assertEqual(normalized["confidence"], 0.8)
        self.assertEqual(
            normalized["policy_checks"][0]["matched_data_need"],
            "payment_identifier_config",
        )

    def test_preserves_non_checklist_prompts(self):
        raw = {
            "policy_id": "SOP-PAY-OP-003",
            "matched_data_need": "van_registration_status",
        }

        normalized = _normalize_checklist_output("case_parser", raw)

        self.assertIs(normalized, raw)


if __name__ == "__main__":
    unittest.main()
