import unittest

from storeops.apps.demo import run_demo_case
from storeops.apps.operator_cli import run, run_view_model
from storeops.apps.operator_web import build_html
from storeops.apps.portfolio_console import build_console_cases, case_queue_rows, count_by_issue
from storeops.apps.release_artifacts import generate_release_artifacts


class AppsPackageTests(unittest.TestCase):
    def test_apps_package_provides_operator_cli_entrypoint(self):
        payload = run("S1")

        self.assertEqual(payload["case_id"], "CASE-S1")
        self.assertEqual(payload["primary_cause"], "duplicate_tid")

    def test_apps_package_provides_operator_web_entrypoint(self):
        html = build_html("S1")

        self.assertIn("StoreOps Triage Agent", html)

    def test_apps_package_provides_demo_entrypoint(self):
        payload = run_demo_case("S5")

        self.assertEqual(payload["state"], "NEEDS_CLARIFICATION")
        self.assertEqual(payload["provider"], "scripted-demo")
        self.assertEqual(len(payload["clarification_questions"]), 2)

    def test_apps_package_provides_release_artifacts_entrypoint(self):
        self.assertTrue(callable(generate_release_artifacts))

    def test_apps_package_provides_portfolio_console_dataset(self):
        cases = build_console_cases()
        rows = case_queue_rows(cases)
        issue_counts = count_by_issue(cases)

        self.assertEqual(len(cases), 8)
        self.assertEqual(rows[0]["case"], "CASE-S1")
        self.assertIn("동일 TID", issue_counts)

    def test_apps_package_provides_view_model_entrypoint(self):
        view_model = run_view_model("S1")

        self.assertEqual(view_model.case_id, "CASE-S1")
        self.assertEqual(view_model.primary_cause, "duplicate_tid")


if __name__ == "__main__":
    unittest.main()
