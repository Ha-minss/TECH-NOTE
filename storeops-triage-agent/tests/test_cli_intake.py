import unittest

from storeops.apps.operator_cli import run


class OperatorCliMaskingTests(unittest.TestCase):
    def test_every_scenario_runs_with_masked_output(self) -> None:
        expected_states = {
            "S1": "READY_FOR_REVIEW",
            "S2": "READY_FOR_REVIEW",
            "S3": "READY_FOR_REVIEW",
            "S4": "READY_FOR_REVIEW",
            "S5": "NEEDS_CLARIFICATION",
            "S6A": "DEGRADED_REVIEW",
            "S6B": "READY_FOR_REVIEW",
            "S7": "CONFLICT_REVIEW",
        }

        for scenario_id, expected_state in expected_states.items():
            with self.subTest(scenario_id=scenario_id):
                payload = run(scenario_id)
                self.assertEqual(expected_state, payload["state"])
                self.assertNotRegex(str(payload), r"TID-\d{6}")


if __name__ == "__main__":
    unittest.main()
