"""Operator review journeys built on top of the offline payment workflow backend."""

from __future__ import annotations

from dataclasses import dataclass

from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.operator.approvals import ApprovalState, ApprovalType
from storeops.operator.handoff import HandoffPackage
from storeops.operator.view_model import OperatorCaseViewModel


@dataclass(frozen=True)
class OperatorReview:
    workflow_result: object
    view_model: OperatorCaseViewModel
    approvals: ApprovalState


class OperatorJourneyService:
    def __init__(self, workflow: OfflinePaymentWorkflow):
        self.workflow = workflow

    @classmethod
    def default(cls, connection) -> "OperatorJourneyService":
        return cls(OfflinePaymentWorkflow.default(connection))

    def review_scenario(
        self,
        scenario_id: str,
        *,
        operator_id: str = "OP-DEMO",
        trace_id: str | None = None,
    ) -> OperatorReview:
        result = self.workflow.run_scenario(
            scenario_id,
            operator_id=operator_id,
            trace_id=trace_id or f"TRACE-{scenario_id}-OP",
        )
        return OperatorReview(
            workflow_result=result,
            view_model=OperatorCaseViewModel.from_workflow_result(result),
            approvals=ApprovalState(),
        )

    def approve(
        self,
        review: OperatorReview,
        approval_type: ApprovalType,
        reviewer_id: str,
    ) -> OperatorReview:
        return OperatorReview(
            workflow_result=review.workflow_result,
            view_model=review.view_model,
            approvals=review.approvals.approve(approval_type, reviewer_id),
        )

    def create_handoff(self, review: OperatorReview) -> HandoffPackage:
        return HandoffPackage.from_view_model(
            review.view_model,
            approvals=review.approvals,
        )


__all__ = ["OperatorJourneyService", "OperatorReview"]
