import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class OperatorCliMaskingSubprocessTests(unittest.TestCase):
    def test_cli_masks_tid_values(self) -> None:
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
        json.loads(completed.stdout)
        self.assertNotIn("TID-000100", completed.stdout)
        self.assertNotRegex(completed.stdout, r"TID-\d{6}")


if __name__ == "__main__":
    unittest.main()
