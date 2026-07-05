import unittest

from storeops import schemas


class SchemaContractTests(unittest.TestCase):
    def test_schema_api_exists(self) -> None:
        expected = [
            "Assessment",
            "CaseBrief",
            "CaseState",
            "CauseAssessment",
            "EvidenceRecord",
            "ToolResponse",
            "WorkflowState",
        ]

        missing = [name for name in expected if not hasattr(schemas, name)]

        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
