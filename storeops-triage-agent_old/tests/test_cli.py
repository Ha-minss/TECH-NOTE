import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class OperatorCliOutputTests(unittest.TestCase):
    def test_s1_cli_prints_structured_case_brief(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "src")
        env["PYTHONUTF8"] = "1"

        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "storeops.apps.operator_cli", "S1"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("CASE-S1", payload["case_id"])
        self.assertEqual("READY_FOR_REVIEW", payload["state"])
        self.assertEqual("duplicate_tid", payload["primary_cause"])


if __name__ == "__main__":
    unittest.main()
