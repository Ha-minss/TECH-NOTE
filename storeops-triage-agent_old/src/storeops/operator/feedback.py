"""Operator feedback model for later evaluation-loop curation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeedbackRecord:
    case_id: str
    cause_verdict: str
    final_cause: str | None = None
    route_verdict: str | None = None
    unnecessary_checklist_items: list[str] = field(default_factory=list)
    missing_checklist_items: list[str] = field(default_factory=list)
    response_edited: bool = False
    edited_response: str | None = None
    reviewer_id: str | None = None

    @property
    def checklist_feedback(self) -> dict[str, str]:
        feedback = {
            item: "unnecessary" for item in self.unnecessary_checklist_items
        }
        feedback.update({item: "missing" for item in self.missing_checklist_items})
        return feedback

    @property
    def is_candidate_for_review_queue(self) -> bool:
        return (
            self.cause_verdict != "correct"
            or self.route_verdict == "incorrect"
            or bool(self.unnecessary_checklist_items)
            or bool(self.missing_checklist_items)
            or self.response_edited
        )


__all__ = ["FeedbackRecord"]