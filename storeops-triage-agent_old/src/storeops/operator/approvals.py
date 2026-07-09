"""Human approval state for operator handoff gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ApprovalType(StrEnum):
    CAUSE = "cause"
    ROUTE = "route"
    RESPONSE = "response"


@dataclass(frozen=True)
class ApprovalEvent:
    approval_type: ApprovalType
    reviewer_id: str
    approved_at: datetime


@dataclass(frozen=True)
class ApprovalState:
    cause_approved: bool = False
    route_approved: bool = False
    response_approved: bool = False
    events: list[ApprovalEvent] = field(default_factory=list)

    @property
    def ready_for_handoff(self) -> bool:
        return self.cause_approved and self.route_approved and self.response_approved

    @property
    def missing_approvals(self) -> list[ApprovalType]:
        missing = []
        if not self.cause_approved:
            missing.append(ApprovalType.CAUSE)
        if not self.route_approved:
            missing.append(ApprovalType.ROUTE)
        if not self.response_approved:
            missing.append(ApprovalType.RESPONSE)
        return missing

    def approve(
        self,
        approval_type: ApprovalType,
        reviewer_id: str,
        *,
        approved_at: datetime | None = None,
    ) -> "ApprovalState":
        approved_at = approved_at or datetime.fromisoformat("2026-06-24T21:00:00+09:00")
        return ApprovalState(
            cause_approved=self.cause_approved or approval_type is ApprovalType.CAUSE,
            route_approved=self.route_approved or approval_type is ApprovalType.ROUTE,
            response_approved=self.response_approved or approval_type is ApprovalType.RESPONSE,
            events=[
                *self.events,
                ApprovalEvent(
                    approval_type=approval_type,
                    reviewer_id=reviewer_id,
                    approved_at=approved_at,
                ),
            ],
        )


__all__ = ["ApprovalEvent", "ApprovalState", "ApprovalType"]
