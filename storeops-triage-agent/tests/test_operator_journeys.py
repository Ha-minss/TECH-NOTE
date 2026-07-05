import unittest

from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.operator.approvals import ApprovalType
from storeops.operator.journeys import OperatorJourneyService
from storeops.core.contracts import WorkflowState


class OperatorJourneyTests(unittest.TestCase):
    def setUp(self):
        self.connection = create_database()
        seed_s1(self.connection)
        seed_offline_payment_scenarios(self.connection)
        self.service = OperatorJourneyService.default(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_s1_journey_can_review_approve_and_create_handoff(self):
        review = self.service.review_scenario("S1")

        self.assertEqual(review.view_model.state, WorkflowState.READY_FOR_REVIEW.value)

        review = self.service.approve(review, ApprovalType.CAUSE, "OP-DEMO")
        review = self.service.approve(review, ApprovalType.ROUTE, "OP-DEMO")
        review = self.service.approve(review, ApprovalType.RESPONSE, "OP-DEMO")
        package = self.service.create_handoff(review)

        self.assertEqual(package.case_id, "CASE-S1")
        self.assertTrue(review.approvals.ready_for_handoff)

    def test_s5_journey_stays_in_clarification_mode_and_has_no_primary_cause(self):
        review = self.service.review_scenario("S5")

        self.assertEqual(review.view_model.state, WorkflowState.NEEDS_CLARIFICATION.value)
        self.assertIsNone(review.view_model.primary_cause)
        self.assertIn("추가 확인", review.view_model.merchant_response_draft)

    def test_s6a_journey_surfaces_degraded_review_for_tool_failure(self):
        review = self.service.review_scenario("S6A")

        self.assertEqual(review.view_model.state, WorkflowState.DEGRADED_REVIEW.value)
        self.assertIsNone(review.view_model.primary_cause)
        self.assertIn("제한적", review.view_model.current_status)

    def test_s7_journey_surfaces_conflict_review_and_conflicting_evidence(self):
        review = self.service.review_scenario("S7")

        self.assertEqual(review.view_model.state, WorkflowState.CONFLICT_REVIEW.value)
        self.assertIsNone(review.view_model.primary_cause)
        self.assertIn("충돌", review.view_model.current_status)
        self.assertTrue(
            any(item["contradicts"] for item in review.view_model.technical_details["evidence"])
        )


if __name__ == "__main__":
    unittest.main()
