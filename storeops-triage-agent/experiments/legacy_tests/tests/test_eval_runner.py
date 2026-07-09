import json
import tempfile
import unittest
from pathlib import Path

from storeops.evals import runner
from storeops.evals.runner import run_full_evaluation


class EvalRunnerTests(unittest.TestCase):
    def test_eval_runner_writes_summary_cases_and_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "latest"
            report = run_full_evaluation(output_dir=output_dir)

            self.assertTrue((output_dir / "summary.json").exists())
            self.assertTrue((output_dir / "cases.json").exists())
            self.assertTrue((output_dir / "report.md").exists())

            summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["total_cases"], report.summary["total_cases"])
            self.assertIn("state_accuracy", summary)

    def test_eval_runner_accepts_synthetic_dataset_and_fixture_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic_50"

            report = run_full_evaluation(
                output_dir=output_dir,
                dataset_path="data/golden/offline_payment_ops_cases_50.json",
                fixture_db_path="data/fixtures/offline_payment_ops_synthetic_50.sqlite3",
            )

            self.assertEqual(report.summary["total_cases"], 50)
            self.assertTrue((output_dir / "summary.json").exists())
            self.assertTrue((output_dir / "cases.json").exists())

    def test_runner_module_exposes_cli_main(self):
        self.assertTrue(callable(runner.main))


if __name__ == "__main__":
    unittest.main()
