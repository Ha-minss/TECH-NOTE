import unittest

from storeops.llm.prompt_contracts import prompt_contract_for


class ChecklistPromptContractTests(unittest.TestCase):
    def test_checklist_contract_requires_schema_envelope(self):
        contract = prompt_contract_for("checklist_extractor")

        self.assertIn("confidence", contract)
        self.assertIn("policy_checks", contract)
        self.assertIn("Do not return a single policy check object", contract)
        self.assertIn("Always wrap every extracted check inside policy_checks", contract)

    def test_checklist_contract_forbids_top_level_policy_check_fields(self):
        contract = prompt_contract_for("checklist_extractor")

        self.assertIn("Do not put policy_id at the top level", contract)
        self.assertIn("Do not put matched_data_need at the top level", contract)
        self.assertIn("Do not put source_quote at the top level", contract)

    def test_checklist_contract_requires_exact_allowed_data_needs(self):
        contract = prompt_contract_for("checklist_extractor")

        self.assertIn("payload.allowed_data_needs", contract)
        self.assertIn("copied exactly from payload.allowed_data_needs", contract)
        self.assertIn("Never create synonyms or new names", contract)
        self.assertIn("merchant_registration_status", contract)


    def test_checklist_contract_requires_complete_sop_coverage(self):
        contract = prompt_contract_for("checklist_extractor")

        self.assertIn("Do not stop after the first policy check", contract)
        self.assertIn("complete evidence coverage", contract)
        self.assertIn("payment_identifier_config", contract)
        self.assertIn("approval_failure_history", contract)
        self.assertIn("Do not include only terminal_inventory", contract)



if __name__ == "__main__":
    unittest.main()
