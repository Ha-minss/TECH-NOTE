"""Operator-facing view models for the final operator review flow.

The UI contract is intentionally result-first:

1. current status
2. cause or abstention
3. next action
4. handoff target
5. merchant response draft
6. evidence summary
7. technical details
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from storeops.core.contracts import WorkflowState


SECTION_ORDER = [
    "current_status",
    "cause_or_abstention",
    "next_action",
    "handoff_target",
    "merchant_response_draft",
    "evidence_summary",
    "technical_details",
]


CAUSE_LABELS = {
    "duplicate_tid": "동일 TID 설정 가능성",
    "terminal_identifier_mismatch": "단말기 식별 정보 불일치 가능성",
    "van_merchant_registration_missing": "가맹점/VAN 등록 상태 확인 필요",
    "pos_front_connection_issue": "POS-Front 연결 문제 가능성",
}


STATE_LABELS = {
    WorkflowState.READY_FOR_REVIEW: "담당자 검토 준비 완료",
    WorkflowState.NEEDS_CLARIFICATION: "추가 정보 확인 필요",
    WorkflowState.DEGRADED_REVIEW: "일부 데이터 조회 실패로 제한적 검토 필요",
    WorkflowState.CONFLICT_REVIEW: "근거 충돌로 사람 재검토 필요",
    WorkflowState.RECEIVED: "접수됨",
    WorkflowState.HUMAN_REVIEW: "사람 검토 중",
    WorkflowState.ROUTE_APPROVED: "이관 경로 승인됨",
    WorkflowState.REJECTED: "처리 반려",
    WorkflowState.HANDED_OFF: "이관 완료",
}


@dataclass(frozen=True)
class OperatorSection:
    key: str
    title: str
    body: str
    severity: str = "info"


@dataclass(frozen=True)
class OperatorCaseViewModel:
    case_id: str
    state: str
    headline: str
    primary_cause: str | None
    assessment: str
    current_status: str
    cause_or_abstention: str
    next_action: str
    recommended_route: str | None
    merchant_response_draft: str
    evidence_count: int
    evidence_ids: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    sections: list[OperatorSection] = field(default_factory=list)
    technical_details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workflow_result(cls, result) -> "OperatorCaseViewModel":
        cause = result.brief.cause
        primary_cause = cause.primary_cause
        current_status = STATE_LABELS.get(result.state.current_state, result.state.current_state.value)
        cause_or_abstention = _cause_or_abstention(result)
        next_action = _next_action(result)
        route = result.brief.recommended_route
        merchant_response = _friendly_merchant_response(result)
        evidence_ids = [record.evidence_id for record in result.evidence]
        headline = _headline(result)
        technical_details = {
            "retrieved_policy_ids": result.retrieved_policy_ids,
            "planned_tools": [call.tool_name for call in result.plan.planned_tool_calls],
            "clarification_questions": list(getattr(result, "clarification_questions", [])),
            "drafted_merchant_response": getattr(result, "drafted_merchant_response", None),
            "llm_traces": [
                {
                    "prompt_name": trace.prompt_name,
                    "model_name": trace.model_name,
                    "status": trace.status,
                    "latency_ms": trace.latency_ms,
                    "used_fallback": trace.used_fallback,
                    "error_message": trace.error_message,
                }
                for trace in getattr(result, "llm_traces", [])
            ],
            "tool_responses": [
                {
                    "tool_name": response.tool_name,
                    "status": response.status.value,
                    "freshness": response.freshness,
                    "warnings": response.warnings,
                }
                for response in result.tool_responses
            ],
            "evidence": [
                {
                    "evidence_id": record.evidence_id,
                    "source_tool": record.source_tool,
                    "fact_type": record.fact_type,
                    "supports": record.supports,
                    "contradicts": record.contradicts,
                }
                for record in result.evidence
            ],
        }
        sections = [
            OperatorSection("current_status", "현재 상태", current_status, _severity(result.state.current_state)),
            OperatorSection("cause_or_abstention", "판단", cause_or_abstention, _severity(result.state.current_state)),
            OperatorSection("next_action", "지금 해야 할 조치", next_action),
            OperatorSection("handoff_target", "담당자 이관 대상", route or "담당자 수동 지정 필요"),
            OperatorSection("merchant_response_draft", "사장님 응답 초안", merchant_response),
            OperatorSection("evidence_summary", "근거 요약", _evidence_summary(result)),
            OperatorSection(
                "technical_details",
                "기술 상세",
                "정책 검색, 도구 호출, EvidenceRecord, Safety Gate 결과를 확인할 수 있습니다.",
            ),
        ]
        return cls(
            case_id=result.state.case_id,
            state=result.state.current_state.value,
            headline=headline,
            primary_cause=primary_cause,
            assessment=cause.assessment.value,
            current_status=current_status,
            cause_or_abstention=cause_or_abstention,
            next_action=next_action,
            recommended_route=route,
            merchant_response_draft=merchant_response,
            evidence_count=len(result.evidence),
            evidence_ids=evidence_ids,
            checklist=list(result.brief.operator_actions),
            sections=sections,
            technical_details=technical_details,
        )


def _headline(result) -> str:
    cause = result.brief.cause.primary_cause
    if cause:
        return f"{CAUSE_LABELS.get(cause, cause)}으로 담당자 검토가 필요합니다."
    if result.state.current_state is WorkflowState.NEEDS_CLARIFICATION:
        return "원인 판단 전 사장님 추가 정보 확인이 필요합니다."
    if result.state.current_state is WorkflowState.CONFLICT_REVIEW:
        return "시점별 시스템 근거가 충돌해 사람 재검토가 필요합니다."
    return "확인 가능한 근거가 부족해 제한적 검토가 필요합니다."


def _cause_or_abstention(result) -> str:
    cause = result.brief.cause.primary_cause
    if cause:
        return f"{CAUSE_LABELS.get(cause, cause)}입니다. 표시된 근거 ID를 확인한 뒤 승인해 주세요."
    missing = result.brief.cause.missing_evidence or result.parsed_case.missing_fields
    if missing:
        return f"현재 확인된 근거만으로는 원인을 확정하기 어렵습니다. 추가 확인 항목: {', '.join(missing)}"
    return "현재 확인된 근거만으로는 원인을 확정하기 어렵습니다."


def _next_action(result) -> str:
    if result.brief.operator_actions:
        return result.brief.operator_actions[0]
    return "담당자가 근거와 누락 정보를 확인합니다."


def _friendly_merchant_response(result) -> str:
    drafted = getattr(result, "drafted_merchant_response", None)
    if drafted:
        return drafted
    cause = result.brief.cause.primary_cause
    if cause:
        return (
            "사장님, 현재 확인된 시스템 기록에서 단말기 설정과 승인 실패 이력을 "
            "담당자가 추가로 확인해야 합니다. 확인 후 필요한 조치를 다시 안내드리겠습니다."
        )
    return (
        "사장님, 현재 확인된 기록만으로는 정확한 원인을 확정하기 어렵습니다. "
        "정확한 파악을 위해 추가 확인이 필요한 정보를 담당자가 확인한 뒤 안내드리겠습니다."
    )


def _evidence_summary(result) -> str:
    if not result.evidence:
        return "아직 원인 판단을 뒷받침할 충분한 시스템 근거가 없습니다."
    ids = ", ".join(record.evidence_id for record in result.evidence)
    return f"총 {len(result.evidence)}개의 근거가 연결되어 있습니다: {ids}"


def _severity(state: WorkflowState) -> str:
    if state is WorkflowState.READY_FOR_REVIEW:
        return "success"
    if state in {WorkflowState.NEEDS_CLARIFICATION, WorkflowState.CONFLICT_REVIEW}:
        return "warning"
    if state is WorkflowState.DEGRADED_REVIEW:
        return "danger"
    return "info"
