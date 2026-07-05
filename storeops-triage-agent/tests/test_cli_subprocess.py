import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class OperatorCliSubprocessTests(unittest.TestCase):
    def test_s4_cli_prints_valid_json_on_windows_console(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "src")
        env["PYTHONUTF8"] = "1"

        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "storeops.apps.operator_cli", "S4"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("READY_FOR_REVIEW", payload["state"])
        self.assertEqual("CASE-S4", payload["case_id"])


if __name__ == "__main__":
    unittest.main()
