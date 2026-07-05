import json
import tempfile
import unittest
from pathlib import Path

from storeops.evals.datasets import load_golden_cases
from storeops.evals.llm_runner import run_llm_evaluation


class LLMEvalRunnerTests(unittest.TestCase):
    def test_golden_cases_cover_s1_through_s7_scenarios(self):
        cases = load_golden_cases()

        self.assertEqual(
            {case.fixture_key for case in cases},
            {"S1", "S2", "S3", "S4", "S5", "S6A", "S6B", "S7"},
        )

    def test_scripted_llm_runner_writes_required_reports_and_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "llm" / "latest"

            report = run_llm_evaluation(output_dir=output_dir, provider="scripted")

            self.assertTrue((output_dir / "summary.json").exists())
            self.assertTrue((output_dir / "cases.json").exists())
            self.assertTrue((output_dir / "report.md").exists())

            summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            cases = json.loads((output_dir / "cases.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["total_cases"], 8)
            self.assertEqual(summary["passed_cases"], report.summary["passed_cases"])
            self.assertEqual(summary["fallback_rate"], 0.0)
            for key in [
                "state_accuracy",
                "cause_accuracy",
                "required_tool_recall",
                "forbidden_action_safety",
                "evidence_citation_coverage",
                "abstention_safety_accuracy",
                "clarification_safety",
                "merchant_response_safety",
                "llm_trace_coverage",
                "fallback_rate",
                "unsupported_claim_count",
            ]:
                self.assertIn(key, summary)

            self.assertEqual(len(cases), 8)
            first = cases[0]
            for key in [
                "case_id",
                "fixture_key",
                "merchant_message",
                "expected_state",
                "actual_state",
                "expected_primary_cause",
                "actual_primary_cause",
                "required_tool_names",
                "actual_tool_names",
                "missing_required_tools",
                "forbidden_actions_triggered",
                "clarification_questions",
                "merchant_response",
                "llm_traces",
                "used_fallback",
                "passed",
                "failure_reasons",
                "policy_check_trace",
            ]:
                self.assertIn(key, first)

            s3 = next(case for case in cases if case["fixture_key"] == "S3")
            tid_trace = [
                item for item in s3["policy_check_trace"]
                if item.get("tool_name") == "get_tid_config"
            ]
            self.assertTrue(tid_trace)
            self.assertEqual(tid_trace[0]["matched_data_need"], "payment_identifier_config")
            self.assertTrue(tid_trace[0]["source_quote"])
            prompt_names = {trace["prompt_name"] for trace in s3["llm_traces"]}
            self.assertIn("checklist_extractor", prompt_names)
            self.assertFalse(s3["used_fallback"])


if __name__ == "__main__":
    unittest.main()
