import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class AllScenariosCliTests(unittest.TestCase):
    def test_all_operator_scenarios_run_from_cli(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "src")
        env["PYTHONUTF8"] = "1"

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
                completed = subprocess.run(
                    [sys.executable, "-X", "utf8", "-m", "storeops.apps.operator_cli", scenario_id],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                payload = json.loads(completed.stdout)
                self.assertEqual(expected_state, payload["state"])
                self.assertNotRegex(completed.stdout, r"TID-\d{6}")


if __name__ == "__main__":
    unittest.main()
