import unittest

from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.operator.approvals import ApprovalState, ApprovalType
from storeops.operator.feedback import FeedbackRecord
from storeops.operator.handoff import HandoffBlockedError, HandoffPackage
from storeops.operator.view_model import OperatorCaseViewModel


class OperatorProductTests(unittest.TestCase):
    def setUp(self):
        self.connection = create_database()
        seed_s1(self.connection)
        seed_offline_payment_scenarios(self.connection)
        self.workflow = OfflinePaymentWorkflow.default(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_view_model_prioritizes_status_cause_action_route_response_and_evidence(self):
        result = self.workflow.run_scenario(
            "S1",
            operator_id="OP-DEMO",
            trace_id="TRACE-OP-S1",
        )

        view = OperatorCaseViewModel.from_workflow_result(result)

        self.assertEqual(
            [section.key for section in view.sections],
            [
                "current_status",
                "cause_or_abstention",
                "next_action",
                "handoff_target",
                "merchant_response_draft",
                "evidence_summary",
                "technical_details",
            ],
        )
        self.assertEqual(view.primary_cause, "duplicate_tid")
        self.assertGreaterEqual(view.evidence_count, 1)

    def test_view_model_uses_friendly_abstention_copy_for_clarification_case(self):
        result = self.workflow.run_scenario(
            "S5",
            operator_id="OP-DEMO",
            trace_id="TRACE-OP-S5",
        )

        view = OperatorCaseViewModel.from_workflow_result(result)

        self.assertIsNone(view.primary_cause)
        self.assertIn("추가 확인 항목", view.cause_or_abstention)
        self.assertIn("사장님", view.merchant_response_draft)

    def test_three_independent_approvals_are_required_for_handoff(self):
        approvals = ApprovalState()

        self.assertFalse(approvals.ready_for_handoff)
        approvals = approvals.approve(ApprovalType.CAUSE, "OP-DEMO")
        approvals = approvals.approve(ApprovalType.ROUTE, "OP-DEMO")
        self.assertFalse(approvals.ready_for_handoff)
        approvals = approvals.approve(ApprovalType.RESPONSE, "OP-DEMO")

        self.assertTrue(approvals.ready_for_handoff)
        self.assertEqual(
            [event.approval_type for event in approvals.events],
            [ApprovalType.CAUSE, ApprovalType.ROUTE, ApprovalType.RESPONSE],
        )

    def test_handoff_package_is_blocked_until_three_approvals_exist(self):
        result = self.workflow.run_scenario(
            "S1",
            operator_id="OP-DEMO",
            trace_id="TRACE-OP-HANDOFF",
        )
        view = OperatorCaseViewModel.from_workflow_result(result)

        with self.assertRaises(HandoffBlockedError):
            HandoffPackage.from_view_model(
                view,
                approvals=ApprovalState().approve(ApprovalType.CAUSE, "OP-DEMO"),
            )

        approvals = (
            ApprovalState()
            .approve(ApprovalType.CAUSE, "OP-DEMO")
            .approve(ApprovalType.ROUTE, "OP-DEMO")
            .approve(ApprovalType.RESPONSE, "OP-DEMO")
        )
        package = HandoffPackage.from_view_model(view, approvals=approvals)

        self.assertEqual(package.case_id, view.case_id)
        self.assertEqual(package.destination, view.recommended_route)
        self.assertEqual(package.evidence_ids, view.evidence_ids)
        self.assertIn(view.headline, package.summary)

    def test_feedback_record_captures_promotion_signals(self):
        feedback = FeedbackRecord(
            case_id="CASE-S1",
            cause_verdict="incorrect",
            final_cause="terminal_identifier_mismatch",
            route_verdict="correct",
            unnecessary_checklist_items=["check_van_registration"],
            missing_checklist_items=["compare_terminal_identity"],
            response_edited=True,
            edited_response="사장님, 담당자가 추가 확인 후 다시 안내드리겠습니다.",
            reviewer_id="OP-DEMO",
        )

        self.assertTrue(feedback.is_candidate_for_review_queue)
        self.assertIn("check_van_registration", feedback.checklist_feedback)
        self.assertEqual(feedback.checklist_feedback["check_van_registration"], "unnecessary")
        self.assertEqual(feedback.checklist_feedback["compare_terminal_identity"], "missing")


if __name__ == "__main__":
    unittest.main()
