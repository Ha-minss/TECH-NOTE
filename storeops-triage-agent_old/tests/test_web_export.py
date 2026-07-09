import tempfile
import unittest
from pathlib import Path

from storeops.apps.operator_web import export_html


class OperatorWebExportTests(unittest.TestCase):
    def test_export_html_writes_operator_demo_page(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "s1.html"
            html = export_html("S1", output_path)

            self.assertTrue(output_path.exists())
            self.assertIn("StoreOps Triage Agent", html)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("Approvals", rendered)
            self.assertIn("Checklist", rendered)
            self.assertIn("EV-S1-DUPLICATE_TID_ASSIGNMENT", rendered)


if __name__ == "__main__":
    unittest.main()
