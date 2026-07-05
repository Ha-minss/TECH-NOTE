import unittest

from storeops.infra.database import create_database
from storeops.core.contracts import Assessment, WorkflowState


class RemainingScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        from storeops.domains.offline_payment_ops.scenario_runtime import seed_all_scenarios

        self.connection = create_database()
        seed_all_scenarios(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def run_case(self, scenario_id: str):
        from storeops.domains.offline_payment_ops.scenario_runtime import run_scenario

        return run_scenario(
            self.connection,
            scenario_id,
            operator_id="OP-DEMO",
            trace_id=f"TRACE-{scenario_id}",
        )

    def test_s2_terminal_identifier_mismatch(self) -> None:
        state, brief = self.run_case("S2")
        self.assertEqual(WorkflowState.READY_FOR_REVIEW, state.current_state)
        self.assertEqual(
            "terminal_identifier_mismatch", brief.cause.primary_cause
        )
        self.assertEqual(Assessment.LIKELY, brief.cause.assessment)
        self.assertNotIn("duplicate_tid", brief.cause.alternative_causes)
        self.assertTrue(brief.cause.supporting_evidence_ids)

    def test_s3_van_registration_missing(self) -> None:
        state, brief = self.run_case("S3")
        self.assertEqual(WorkflowState.READY_FOR_REVIEW, state.current_state)
        self.assertEqual(
            "van_merchant_registration_missing", brief.cause.primary_cause
        )
        self.assertEqual(Assessment.LIKELY, brief.cause.assessment)

    def test_s4_pos_front_connection_failure(self) -> None:
        state, brief = self.run_case("S4")
        self.assertEqual(WorkflowState.READY_FOR_REVIEW, state.current_state)
        self.assertEqual(
            "pos_front_connection_issue", brief.cause.primary_cause
        )
        self.assertEqual(Assessment.LIKELY, brief.cause.assessment)
        self.assertNotIn("get_payment_key_state", state.tool_calls)

    def test_s5_asks_only_for_merchant_only_information(self) -> None:
        state, brief = self.run_case("S5")
        self.assertEqual(WorkflowState.NEEDS_CLARIFICATION, state.current_state)
        self.assertIsNone(brief.cause.primary_cause)
        self.assertEqual(Assessment.UNAVAILABLE, brief.cause.assessment)
        self.assertEqual(
            {"failed_physical_terminal", "visible_error_message"},
            set(brief.cause.missing_evidence),
        )
        rendered = " ".join(brief.operator_actions)
        self.assertNotIn("store ID", rendered)
        self.assertNotIn("TID를 알려", rendered)

    def test_s6a_required_tool_failure_degrades(self) -> None:
        state, brief = self.run_case("S6A")
        self.assertEqual(WorkflowState.DEGRADED_REVIEW, state.current_state)
        self.assertIsNone(brief.cause.primary_cause)
        self.assertEqual(Assessment.UNAVAILABLE, brief.cause.assessment)
        self.assertIn("get_tid_config", brief.cause.missing_evidence)

    def test_s6b_optional_route_failure_preserves_cause(self) -> None:
        state, brief = self.run_case("S6B")
        self.assertEqual(WorkflowState.READY_FOR_REVIEW, state.current_state)
        self.assertEqual("duplicate_tid", brief.cause.primary_cause)
        self.assertEqual(Assessment.LIKELY, brief.cause.assessment)
        self.assertIsNone(brief.recommended_route)

    def test_s7_temporal_conflict_does_not_force_one_cause(self) -> None:
        state, brief = self.run_case("S7")
        self.assertEqual(WorkflowState.CONFLICT_REVIEW, state.current_state)
        self.assertIsNone(brief.cause.primary_cause)
        self.assertEqual(
            Assessment.NEEDS_CONFIRMATION, brief.cause.assessment
        )
        self.assertIn("temporary_duplicate_tid", brief.cause.alternative_causes)
        self.assertGreaterEqual(len(brief.cause.alternative_causes), 2)

    def test_operational_rows_do_not_contain_diagnosis_fields(self) -> None:
        table_names = [
            "terminals",
            "terminal_identities",
            "tid_assignments",
            "installation_events",
            "activation_events",
            "approval_events",
            "van_registrations",
            "pos_front_links",
            "pos_front_connection_events",
        ]
        forbidden_column_names = {"root_cause", "diagnosis", "expected_cause"}

        for table_name in table_names:
            columns = {
                row["name"]
                for row in self.connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
            }
            self.assertTrue(
                columns,
                f"{table_name} must exist and contain columns",
            )
            self.assertTrue(
                forbidden_column_names.isdisjoint(columns),
                f"{table_name} leaks diagnosis metadata",
            )


if __name__ == "__main__":
    unittest.main()
