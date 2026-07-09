import unittest

from storeops.apps.operator_cli import run_view_model
from storeops.operator.web_ui import render_operator_case_html


class OperatorWebUiTests(unittest.TestCase):
    def test_web_ui_renders_case_sections_and_approvals(self):
        view_model = run_view_model("S1")

        html = render_operator_case_html(view_model)

        self.assertIn("StoreOps Triage Agent", html)
        self.assertIn("Approvals", html)
        self.assertIn("Checklist", html)
        self.assertIn("Evidence IDs", html)
        self.assertIn(view_model.headline, html)


if __name__ == "__main__":
    unittest.main()
