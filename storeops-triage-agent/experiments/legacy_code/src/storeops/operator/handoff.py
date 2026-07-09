"""Handoff package model for reviewed operator cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from storeops.operator.approvals import ApprovalState


class HandoffBlockedError(RuntimeError):
    """Raised when handoff is requested before human approvals are complete."""


@dataclass(frozen=True)
class HandoffPackage:
    case_id: str
    destination: str | None
    summary: str
    merchant_response: str
    evidence_ids: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)

    @classmethod
    def from_view_model(
        cls,
        view_model,
        *,
        approvals: ApprovalState,
    ) -> "HandoffPackage":
        if not approvals.ready_for_handoff:
            missing = ", ".join(item.value for item in approvals.missing_approvals)
            raise HandoffBlockedError(f"Handoff requires approvals: {missing}")
        return cls(
            case_id=view_model.case_id,
            destination=view_model.recommended_route,
            summary=f"{view_model.headline}\n\n{view_model.cause_or_abstention}",
            merchant_response=view_model.merchant_response_draft,
            evidence_ids=list(view_model.evidence_ids),
            checklist=list(view_model.checklist),
        )


__all__ = ["HandoffBlockedError", "HandoffPackage"]
