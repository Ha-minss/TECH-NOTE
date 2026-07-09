import unittest
from pathlib import Path


class DocumentContractAlignmentTests(unittest.TestCase):
    def test_implemented_scenarios_are_named_in_both_contracts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        scenario_contract = (root / "docs" / "scenario-contract.md").read_text(
            encoding="utf-8"
        )
        data_contract = (root / "docs" / "data-contract.md").read_text(
            encoding="utf-8"
        )

        for scenario_id in ("S2", "S3", "S4", "S5", "S6A", "S6B", "S7"):
            with self.subTest(scenario_id=scenario_id):
                self.assertIn(scenario_id, scenario_contract)
                self.assertIn(scenario_id, data_contract)

    def test_contract_safety_terms_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        combined = "\n".join(
            [
                (root / "docs" / "scenario-contract.md").read_text(
                    encoding="utf-8"
                ),
                (root / "docs" / "data-contract.md").read_text(
                    encoding="utf-8"
                ),
            ]
        )

        for term in (
            "required_tools",
            "forbidden_tools",
            "NEEDS_CLARIFICATION",
            "DEGRADED_REVIEW",
            "CONFLICT_REVIEW",
            "root_cause",
            "store_id",
            "tool_failure_injections",
        ):
            with self.subTest(term=term):
                self.assertIn(term, combined)


if __name__ == "__main__":
    unittest.main()
