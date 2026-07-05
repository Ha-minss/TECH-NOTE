import unittest

from storeops.evals.datasets import GoldenCase, load_golden_cases
from storeops.evals.deterministic import DeterministicEvaluator


class DeterministicEvalTests(unittest.TestCase):
    def test_golden_cases_load_from_default_dataset(self):
        cases = load_golden_cases()

        self.assertGreaterEqual(len(cases), 4)
        self.assertTrue(all(isinstance(case, GoldenCase) for case in cases))
        self.assertIn("GOLD-S1-001", {case.case_id for case in cases})

    def test_deterministic_evaluator_scores_baseline_cases(self):
        cases = load_golden_cases()
        evaluator = DeterministicEvaluator.default()

        results = [evaluator.evaluate_case(case) for case in cases]

        self.assertTrue(all(result.has_trace for result in results))
        self.assertTrue(all(result.forbidden_action_count == 0 for result in results))
        self.assertTrue(all(result.has_evidence_citations or result.actual_state != "READY_FOR_REVIEW" for result in results))
        self.assertTrue(any(result.actual_state == "CONFLICT_REVIEW" for result in results))


if __name__ == "__main__":
    unittest.main()
