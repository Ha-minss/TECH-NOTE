"""Explicit review-state transition rules."""

from __future__ import annotations

from enum import StrEnum

from storeops.core.contracts import WorkflowState


class ReviewState(StrEnum):
    HUMAN_REVIEW = WorkflowState.HUMAN_REVIEW.value
    ROUTE_APPROVED = WorkflowState.ROUTE_APPROVED.value


class InvalidStateTransition(ValueError):
    """Raised when a workflow attempts an impossible transition."""


StateLike = WorkflowState | ReviewState


ALLOWED_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.RECEIVED: {
        WorkflowState.READY_FOR_REVIEW,
        WorkflowState.NEEDS_CLARIFICATION,
        WorkflowState.DEGRADED_REVIEW,
        WorkflowState.CONFLICT_REVIEW,
        WorkflowState.REJECTED,
    },
    WorkflowState.NEEDS_CLARIFICATION: {
        WorkflowState.RECEIVED,
        WorkflowState.REJECTED,
    },
    WorkflowState.READY_FOR_REVIEW: {WorkflowState.HUMAN_REVIEW},
    WorkflowState.DEGRADED_REVIEW: {WorkflowState.HUMAN_REVIEW},
    WorkflowState.CONFLICT_REVIEW: {WorkflowState.HUMAN_REVIEW},
    WorkflowState.HUMAN_REVIEW: {
        WorkflowState.HUMAN_REVIEW,
        WorkflowState.ROUTE_APPROVED,
    },
    WorkflowState.ROUTE_APPROVED: {WorkflowState.HANDED_OFF},
    WorkflowState.REJECTED: set(),
    WorkflowState.HANDED_OFF: set(),
}


def _normalize(state: StateLike) -> WorkflowState:
    if isinstance(state, WorkflowState):
        return state
    return WorkflowState(state.value)


def transition(current: StateLike, target: StateLike) -> WorkflowState:
    normalized_current = _normalize(current)
    normalized_target = _normalize(target)
    if normalized_target not in ALLOWED_TRANSITIONS.get(normalized_current, set()):
        raise InvalidStateTransition(f"{normalized_current} -> {normalized_target} is not allowed")
    return normalized_target


__all__ = [
    "ALLOWED_TRANSITIONS",
    "InvalidStateTransition",
    "ReviewState",
    "StateLike",
    "transition",
]
