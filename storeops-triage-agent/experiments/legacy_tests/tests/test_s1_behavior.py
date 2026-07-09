import unittest

from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.core.contracts import Assessment, ToolStatus, WorkflowState
from storeops.infra.tools import ToolGateway


class S1BehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_database()
        seed_s1(self.connection)
        seed_offline_payment_scenarios(self.connection)
        self.gateway = ToolGateway(
            self.connection,
            operator_id="OP-DEMO",
            trace_id="TRACE-S1",
        )

    def tearDown(self) -> None:
        self.connection.close()

    def test_s1_workflow_produces_grounded_duplicate_tid_brief(self) -> None:
        result = OfflinePaymentWorkflow.default(self.connection).run_scenario(
            "S1",
            operator_id="OP-DEMO",
            trace_id="TRACE-S1",
        )

        self.assertEqual(WorkflowState.READY_FOR_REVIEW, result.state.current_state)
        self.assertEqual("duplicate_tid", result.brief.cause.primary_cause)
        self.assertEqual(Assessment.LIKELY, result.brief.cause.assessment)
        self.assertEqual(
            {"EV-S1-DUPLICATE_TID_ASSIGNMENT"},
            set(result.brief.cause.supporting_evidence_ids),
        )
        self.assertEqual(1, len(result.evidence))
        self.assertNotIn("root_cause", str(result.evidence))
        self.assertIn(
            "change_tid_without_confirmation",
            result.brief.cause.forbidden_actions,
        )
        self.assertIsNotNone(result.brief.recommended_route)

    def test_store_scope_blocks_unauthorized_access(self) -> None:
        response = self.gateway.get_terminals("STR-NOT-AUTHORIZED")

        self.assertEqual(ToolStatus.ERROR, response.status)
        self.assertIsNotNone(response.error)
        self.assertEqual(
            "ToolAuthorizationError",
            response.error.error_type,
        )

    def test_s1_fixture_contains_raw_facts_not_diagnosis_labels(self) -> None:
        tables = [
            "terminals",
            "tid_assignments",
            "activation_events",
            "approval_events",
        ]

        serialized = []
        for table in tables:
            rows = self.connection.execute(f"SELECT * FROM {table}").fetchall()
            serialized.extend(str(dict(row)) for row in rows)

        raw_fixture = "\n".join(serialized).lower()
        self.assertNotIn("root_cause", raw_fixture)
        self.assertNotIn("duplicate_tid", raw_fixture)


if __name__ == "__main__":
    unittest.main()
