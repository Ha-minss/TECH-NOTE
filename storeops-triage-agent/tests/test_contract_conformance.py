import unittest

from storeops.infra.database import create_database
from storeops.domains.offline_payment_ops.scenario_runtime import run_scenario, seed_all_scenarios


class ContractConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_database()
        seed_all_scenarios(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def run_case(self, scenario_id: str):
        return run_scenario(
            self.connection,
            scenario_id,
            operator_id="OP-DEMO",
            trace_id=f"TRACE-CONTRACT-{scenario_id}",
        )

    def test_s2_fixture_has_distinct_tids_and_identity_mismatch(self) -> None:
        tids = self.connection.execute(
            "SELECT tid FROM tid_assignments WHERE store_id = 'STR-S2'"
        ).fetchall()
        mismatch = self.connection.execute(
            """
            SELECT 1
            FROM terminals t
            JOIN terminal_identities i ON i.terminal_id = t.terminal_id
            WHERE t.store_id = 'STR-S2'
              AND (
                t.device_number != i.registered_device_number
                OR t.physical_serial != i.registered_serial
              )
            """
        ).fetchone()
        self.assertEqual(len(tids), len({row["tid"] for row in tids}))
        self.assertIsNotNone(mismatch)

    def test_s3_fixture_has_valid_identity_and_incomplete_van(self) -> None:
        mismatch_count = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM terminals t
            JOIN terminal_identities i ON i.terminal_id = t.terminal_id
            WHERE t.store_id = 'STR-S3'
              AND (
                t.device_number != i.registered_device_number
                OR t.physical_serial != i.registered_serial
              )
            """
        ).fetchone()["count"]
        van_status = self.connection.execute(
            "SELECT registration_status FROM van_registrations WHERE store_id = 'STR-S3'"
        ).fetchone()["registration_status"]
        self.assertEqual(0, mismatch_count)
        self.assertIn(van_status, {"not_registered", "pending", "inactive"})

    def test_s4_fixture_rules_out_tid_identity_and_van_before_connection(self) -> None:
        tid_count = self.connection.execute(
            "SELECT COUNT(DISTINCT tid) AS count FROM tid_assignments WHERE store_id = 'STR-S4'"
        ).fetchone()["count"]
        terminal_count = self.connection.execute(
            "SELECT COUNT(*) AS count FROM terminals WHERE store_id = 'STR-S4'"
        ).fetchone()["count"]
        van_status = self.connection.execute(
            "SELECT registration_status FROM van_registrations WHERE store_id = 'STR-S4'"
        ).fetchone()["registration_status"]
        self.assertEqual(terminal_count, tid_count)
        self.assertEqual("active", van_status)

    def test_s5_tools_cannot_identify_failed_physical_terminal(self) -> None:
        linked_errors = self.connection.execute(
            "SELECT COUNT(*) AS count FROM approval_events WHERE store_id = 'STR-S5'"
        ).fetchone()["count"]
        state, _ = self.run_case("S5")
        self.assertEqual(0, linked_errors)
        self.assertIn("get_store_info", state.tool_calls)

    def test_s6_variants_record_required_and_supporting_tool_attempts(self) -> None:
        state_a, _ = self.run_case("S6A")
        state_b, _ = self.run_case("S6B")
        for tool_name in {
            "get_tid_config",
            "get_activation_history",
            "get_recent_approval_errors",
        }:
            self.assertIn(tool_name, state_a.tool_calls)
        for tool_name in {
            "get_terminals",
            "get_tid_config",
            "get_activation_history",
            "get_recent_approval_errors",
            "get_support_route",
        }:
            self.assertIn(tool_name, state_b.tool_calls)

    def test_scenario_metadata_is_separate_from_operational_tables(self) -> None:
        scenario_rows = self.connection.execute(
            "SELECT scenario_id, expected_state FROM scenarios"
        ).fetchall()
        mapping_rows = self.connection.execute(
            "SELECT scenario_id, store_id FROM scenario_stores"
        ).fetchall()
        self.assertEqual(8, len(scenario_rows))
        self.assertEqual(8, len(mapping_rows))


if __name__ == "__main__":
    unittest.main()
