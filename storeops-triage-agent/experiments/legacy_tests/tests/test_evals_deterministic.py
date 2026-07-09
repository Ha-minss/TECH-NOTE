import unittest
from pathlib import Path

from storeops.evals.datasets import GoldenCase, load_golden_cases
from storeops.evals.deterministic import DeterministicEvaluator
from storeops.infra.database import open_database


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

    def test_synthetic_golden_cases_load_script_key(self):
        dataset_path = Path("data/golden/offline_payment_ops_cases_50.json")

        cases = load_golden_cases(dataset_path)

        self.assertEqual(len(cases), 50)
        self.assertEqual(cases[0].fixture_key, "SYN-001")
        self.assertEqual(cases[0].script_key, "S1")

    def test_open_database_reads_existing_fixture_and_store_mapping(self):
        fixture_path = Path("data/fixtures/offline_payment_ops_synthetic_50.sqlite3")

        connection = open_database(fixture_path)
        try:
            store_id = DeterministicEvaluator.from_fixture_db(fixture_path)._store_id_for(
                connection,
                "SYN-001",
            )
        finally:
            connection.close()

        self.assertEqual(store_id, "STR-SYN-001")


if __name__ == "__main__":
    unittest.main()
