import unittest

from storeops.infra.database import create_database
from storeops.infra.fixture_validation import FixtureValidationError, validate_fixtures
from storeops.domains.offline_payment_ops.scenario_runtime import seed_all_scenarios


class FixtureValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_database()
        seed_all_scenarios(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def test_valid_synthetic_fixtures_pass(self) -> None:
        report = validate_fixtures(self.connection)

        self.assertTrue(report.valid)
        self.assertEqual([], report.errors)
        self.assertEqual(
            {"S1", "S2", "S3", "S4", "S5", "S6A", "S6B", "S7"},
            set(report.scenarios_checked),
        )

    def test_diagnosis_column_in_operational_table_is_rejected(self) -> None:
        self.connection.execute(
            "ALTER TABLE approval_events ADD COLUMN root_cause TEXT"
        )

        with self.assertRaises(FixtureValidationError):
            validate_fixtures(self.connection, raise_on_error=True)

    def test_cross_store_terminal_reference_is_rejected(self) -> None:
        self.connection.execute(
            """
            UPDATE tid_assignments
            SET store_id = 'STR-S3'
            WHERE tid_assignment_id = 'TIDA-S2-OLD'
            """
        )

        report = validate_fixtures(self.connection)

        self.assertFalse(report.valid)
        self.assertTrue(
            any("cross-store" in error for error in report.errors),
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()
