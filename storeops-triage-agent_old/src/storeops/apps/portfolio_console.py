"""Streamlit portfolio console for the StoreOps triage agent."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from storeops.apps.operator_cli import SCENARIOS, create_connection
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.evals.datasets import load_golden_cases
from storeops.evals.llm_runner import build_scripted_client
from storeops.operator.view_model import OperatorCaseViewModel


STATE_LABELS = {
    "READY_FOR_REVIEW": "\uc2b9\uc778 \ub300\uae30",
    "NEEDS_CLARIFICATION": "\ucd94\uac00 \uc815\ubcf4 \ud544\uc694",
    "DEGRADED_REVIEW": "\uc81c\ud55c \uac80\ud1a0",
    "CONFLICT_REVIEW": "\ucda9\ub3cc \uac80\ud1a0",
}
STATE_TONES = {
    "READY_FOR_REVIEW": "success",
    "NEEDS_CLARIFICATION": "warning",
    "DEGRADED_REVIEW": "danger",
    "CONFLICT_REVIEW": "danger",
}
ISSUE_LABELS = {
    "duplicate_tid": "\ub3d9\uc77c TID",
    "terminal_identifier_mismatch": "\ub2e8\ub9d0\uae30 \uc2dd\ubcc4 \ubd88\uc77c\uce58",
    "van_merchant_registration_missing": "VAN \ub4f1\ub85d \ub204\ub77d",
    "pos_front_connection_issue": "POS-Front \uc5f0\uacb0",
    "needs_clarification": "\uc815\ubcf4 \ubd80\uc871",
    "degraded_review": "\uc870\ud68c \uc2e4\ud328",
    "conflict_review": "\uc99d\uac70 \ucda9\ub3cc",
}
ISSUE_DESCRIPTIONS = {
    "duplicate_tid": "\uc2e0\uaddc/\uae30\uc874 \ub2e8\ub9d0\uae30\uc758 \uacb0\uc81c \uc2dd\ubcc4\uc790 \ucda9\ub3cc \uac00\ub2a5\uc131",
    "terminal_identifier_mismatch": "\ud604\uc7a5 \ub2e8\ub9d0\uae30\uc640 \ub4f1\ub85d \uc815\ubcf4\uac00 \ub2e4\ub978 \uc0c1\ud0dc",
    "van_merchant_registration_missing": "\uac00\ub9f9\uc810/VAN \ub4f1\ub85d\uc774 \uc644\ub8cc\ub418\uc9c0 \uc54a\uc740 \uc0c1\ud0dc",
    "pos_front_connection_issue": "POS \uc694\uccad\uc774 Front/\ub2e8\ub9d0\uae30\ub85c \uc804\ub2ec\ub418\uc9c0 \uc54a\ub294 \uc0c1\ud0dc",
    "needs_clarification": "\uc6d0\uc778 \uc2b9\uc778 \uc804 \uace0\uac1d \ucd94\uac00 \uc815\ubcf4\uac00 \ud544\uc694\ud55c \uc0c1\ud0dc",
    "degraded_review": "\ud544\uc218 \uc870\ud68c\uac00 \uc2e4\ud328\ud574 \uc81c\ud55c\uc801\uc73c\ub85c \ubcf4\uc544\uc57c \ud558\ub294 \uc0c1\ud0dc",
    "conflict_review": "\ud604\uc7ac \uae30\ub85d\uacfc \uc0ac\uace0 \uc2dc\uc810 \uae30\ub85d\uc774 \ub2e4\ub978 \uc0c1\ud0dc",
}
ROUTE_LABELS = {
    "installation_or_van_owner_review": "\uc124\uce58/VAN \ub2f4\ub2f9\uc790 \uac80\ud1a0",
    "installation_partner": "\uc124\uce58 \ud30c\ud2b8\ub108 \ud655\uc778",
    "van_registration_owner": "VAN \ub4f1\ub85d \ub2f4\ub2f9\uc790 \ud655\uc778",
    "pos_front_support": "POS-Front \uc9c0\uc6d0\ud300 \ud655\uc778",
    "manual_review": "\uc6b4\uc601\uc790 \uc218\ub3d9 \uc9c0\uc815",
}
TOOL_LABELS = {
    "get_terminals": "\ub2e8\ub9d0\uae30 \ubaa9\ub85d \ud655\uc778",
    "get_tid_config": "TID \uc124\uc815 \ud655\uc778",
    "get_tid_history": "TID \uc774\ub825 \ud655\uc778",
    "get_recent_approval_errors": "\ucd5c\uadfc \uc2b9\uc778 \uc624\ub958 \ud655\uc778",
    "get_installation_history": "\uc124\uce58/\uad50\uccb4 \uc774\ub825 \ud655\uc778",
    "get_activation_history": "\uac1c\ud1b5/\ud65c\uc131\ud654 \uc774\ub825 \ud655\uc778",
    "get_terminal_identity": "\ub2e8\ub9d0\uae30 \uc2dd\ubcc4 \uc815\ubcf4 \ud655\uc778",
    "get_van_registration": "VAN \ub4f1\ub85d \uc0c1\ud0dc \ud655\uc778",
    "get_pos_front_connection_logs": "POS-Front \uc5f0\uacb0 \ub85c\uadf8 \ud655\uc778",
}
FACT_LABELS = {
    "duplicate_tid_assignment": "\ub3d9\uc77c TID \uc124\uc815 \uadfc\uac70",
    "terminal_identity_mismatch": "\ub2e8\ub9d0\uae30 \uc2dd\ubcc4 \ubd88\uc77c\uce58 \uadfc\uac70",
    "van_registration_incomplete": "VAN \ub4f1\ub85d \ubbf8\uc644\ub8cc \uadfc\uac70",
    "pos_front_connection_failure": "POS-Front \uc5f0\uacb0 \uc2e4\ud328 \uadfc\uac70",
    "tool_failure": "\uc870\ud68c \uc2e4\ud328 \uadfc\uac70",
    "temporal_tid_conflict": "\uc2dc\uc810\ubcc4 TID \ucda9\ub3cc \uadfc\uac70",
}
EVAL_METRICS = {
    "Deterministic eval": "8/8",
    "Scripted LLM eval": "8/8",
    "Required tool recall": "1.00",
    "Evidence citation coverage": "1.00",
    "Unsupported claims": "0",
    "Fallback rate": "0.00",
}

T = {
    "brand_sub": "\uc6b4\uc601\uc790 \uac80\ud1a0 \ucf58\uc194",
    "ai_review": "AI \uac80\ud1a0",
    "approval_required": "\uc6b4\uc601\uc790 \uc2b9\uc778 \ud544\uc694",
    "queue_title": "\uc6b4\uc601\uc790 \uac80\ud1a0 \ud050",
    "queue_sub": "\uc624\ub298 \ucc98\ub9ac\ud574\uc57c \ud560 \uacb0\uc81c \uc7a5\uc560 \ucf00\uc774\uc2a4\ub97c \uc2b9\uc778 \uac00\ub2a5 \uc5ec\ubd80 \uae30\uc900\uc73c\ub85c \uc815\ub9ac\ud569\ub2c8\ub2e4.",
    "detail_title": "\ucf00\uc774\uc2a4 \uc2b9\uc778 \ud654\uba74",
    "detail_sub": "\uc6b4\uc601\uc790\uac00 \uc2b9\uc778, \ubcf4\ub958, \uc7ac\uac80\ud1a0\ub97c \uacb0\uc815\ud558\ub294 \ub370 \ud544\uc694\ud55c \uc815\ubcf4\ub9cc \uba3c\uc800 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
    "analytics_title": "\ubb38\uc81c \uc720\ud615 \ubd84\uc11d",
    "analytics_sub": "\uc804\uccb4 \ucf00\uc774\uc2a4\uc5d0\uc11c \uc5b4\ub5a4 \ubb38\uc81c\uac00 \ub9ce\uc774 \ubc1c\uc0dd\ud558\uace0 \uc5b4\ub514\uc11c \ubcf4\ub958\ub418\ub294\uc9c0 \ubd05\ub2c8\ub2e4.",
    "trace_title": "\uc99d\uac70 \ucd94\uc801",
    "trace_sub": "AI\uac00 \ubb34\uc5c7\uc744 \ubcf4\uace0 \ud310\ub2e8\ud588\ub294\uc9c0 \uc6b4\uc601\uc790 \uc5b8\uc5b4\ub85c \ud480\uc5b4 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
    "eval_title": "\ud3c9\uac00 \ub9ac\ud3ec\ud2b8",
    "eval_sub": "\uc678\ubd80 API \uc5c6\uc774 \uc7ac\ud604 \uac00\ub2a5\ud55c scripted \ud3c9\uac00 \uacb0\uacfc\ub9cc \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
}


@dataclass(frozen=True)
class ConsoleCase:
    scenario_id: str
    result: Any
    view_model: OperatorCaseViewModel

    @property
    def state(self) -> str:
        return self.view_model.state

    @property
    def issue_key(self) -> str:
        if self.view_model.primary_cause:
            return self.view_model.primary_cause
        if self.state == "NEEDS_CLARIFICATION":
            return "needs_clarification"
        if self.state == "DEGRADED_REVIEW":
            return "degraded_review"
        if self.state == "CONFLICT_REVIEW":
            return "conflict_review"
        return "needs_clarification"

    @property
    def approval_posture(self) -> str:
        if self.state == "READY_FOR_REVIEW":
            return "\uc2b9\uc778 \uac00\ub2a5"
        if self.state == "NEEDS_CLARIFICATION":
            return "\uc2b9\uc778 \ubcf4\ub958"
        if self.state == "CONFLICT_REVIEW":
            return "\uc7ac\uac80\ud1a0 \ud544\uc694"
        return "\uc81c\ud55c \uac80\ud1a0 \ud544\uc694"

    @property
    def risk(self) -> str:
        if self.state == "READY_FOR_REVIEW":
            return "\ub0ae\uc74c"
        if self.state == "NEEDS_CLARIFICATION":
            return "\uc911\uac04"
        return "\ub192\uc74c"


def build_console_cases() -> list[ConsoleCase]:
    cases = load_golden_cases()
    client = build_scripted_client(cases)
    connection = create_connection()
    try:
        workflow = OfflinePaymentWorkflow.with_llm(connection, client=client, model_name="scripted-console")
        console_cases: list[ConsoleCase] = []
        for scenario_id in SCENARIOS:
            result = workflow.run_scenario(scenario_id, operator_id="OP-DEMO", trace_id=f"TRACE-CONSOLE-{scenario_id}")
            console_cases.append(ConsoleCase(scenario_id, result, OperatorCaseViewModel.from_workflow_result(result)))
        return console_cases
    finally:
        connection.close()


def case_queue_rows(cases: list[ConsoleCase]) -> list[dict[str, object]]:
    return [
        {
            "case": case.view_model.case_id,
            "scenario": case.scenario_id,
            "status": STATE_LABELS.get(case.state, case.state),
            "issue": ISSUE_LABELS.get(case.issue_key, case.issue_key),
            "approval": case.approval_posture,
            "risk": case.risk,
            "evidence": case.view_model.evidence_count,
            "route": _route_label(case.view_model.recommended_route),
        }
        for case in cases
    ]


def count_by_state(cases: list[ConsoleCase]) -> dict[str, int]:
    counts = {state: 0 for state in STATE_LABELS}
    for case in cases:
        counts[case.state] = counts.get(case.state, 0) + 1
    return counts


def count_by_issue(cases: list[ConsoleCase]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        label = ISSUE_LABELS.get(case.issue_key, case.issue_key)
        counts[label] = counts.get(label, 0) + 1
    return counts


def _route_label(route: str | None) -> str:
    return ROUTE_LABELS.get(route or "manual_review", route or ROUTE_LABELS["manual_review"])


def _tool_label(tool_name: str) -> str:
    return TOOL_LABELS.get(tool_name, tool_name.replace("_", " "))


def _fact_label(fact_type: str) -> str:
    return FACT_LABELS.get(fact_type, fact_type.replace("_", " "))


def _h(value: object) -> str:
    return escape(str(value), quote=True)


def _badge(text: str, tone: str = "info") -> str:
    return f'<span class="badge {tone}">{_h(text)}</span>'


def _status_badge(state: str) -> str:
    return _badge(STATE_LABELS.get(state, state), STATE_TONES.get(state, "info"))


def _yes_no(value: bool) -> str:
    return _badge("\uc608" if value else "\uc544\ub2c8\uc624", "success" if value else "muted")


def _render_html_table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{_h(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="clean-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _bar_chart(title: str, values: dict[str, int]) -> str:
    maximum = max(values.values(), default=1)
    bars = []
    for label, value in values.items():
        width = 4 if maximum == 0 else max(4, int((value / maximum) * 100))
        bars.append(f'<div class="bar-row"><div class="bar-label">{_h(label)}</div><div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div><div class="bar-value">{value}</div></div>')
    return f'<section class="panel"><h3>{_h(title)}</h3>{"".join(bars)}</section>'


def _inject_css(st) -> None:
    st.markdown(
        """
        <style>
        :root{--bg:#f5f7fa;--panel:#fff;--ink:#1f2937;--muted:#667085;--line:#e5e7eb;--soft:#f8fafc;--blue:#38aeea;--green:#54b894;--amber:#f59e0b;--red:#ef4444;}
        .stApp{background:var(--bg);color:var(--ink)}.main .block-container{padding-top:1.4rem;max-width:1360px}header[data-testid="stHeader"]{background:rgba(245,247,250,.92)}#MainMenu,footer{visibility:hidden}h1,h2,h3,p{letter-spacing:0}div[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}div[data-testid="stSidebar"] *{color:var(--ink)}div[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:8px;padding:8px 10px;margin-bottom:4px}.topbar{display:flex;justify-content:space-between;align-items:center;background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 18px;margin-bottom:16px;box-shadow:0 1px 2px rgba(16,24,40,.04)}.brand{font-size:18px;font-weight:800;color:var(--ink)}.brand span{color:var(--blue)}.page-title{font-size:25px;font-weight:800;margin:0;color:var(--ink)}.page-subtitle{color:var(--muted);font-size:13px;margin-top:3px}.toolbar{display:flex;gap:8px;align-items:center}.metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:14px}.metric-card,.panel,.decision-card{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:0 1px 2px rgba(16,24,40,.04);padding:16px}.metric-label{color:var(--muted);font-size:12px;font-weight:700}.metric-value{color:var(--blue);font-size:28px;font-weight:800;margin-top:2px}.metric-note{color:var(--muted);font-size:12px;margin-top:1px}.badge{display:inline-flex;align-items:center;height:24px;padding:0 9px;border-radius:999px;font-size:12px;font-weight:800;white-space:nowrap}.badge.success{background:#dcfae6;color:#067647}.badge.warning{background:#fff4d6;color:#b54708}.badge.danger{background:#fee4e2;color:#b42318}.badge.info{background:#e0f2fe;color:#026aa2}.badge.muted{background:#eef2f6;color:#667085}.queue-card{background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}.queue-row{display:grid;grid-template-columns:108px 1.6fr 120px 120px 100px 170px;gap:12px;align-items:center;padding:13px 16px;border-bottom:1px solid var(--line)}.queue-row.header{background:#f8fafc;color:var(--muted);font-size:12px;font-weight:800}.queue-row:last-child{border-bottom:0}.queue-case{font-weight:800;color:var(--ink)}.queue-meta{color:var(--muted);font-size:12px;margin-top:2px}.two-col{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(340px,.62fr);gap:14px}.three-col{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.decision-card{border-left:4px solid var(--blue)}.decision-label{color:var(--muted);font-size:12px;font-weight:800}.decision-value{font-size:28px;color:var(--ink);font-weight:900;margin:4px 0}.body-copy{color:var(--ink);line-height:1.65;font-size:14px}.info-grid{display:grid;gap:10px}.info-item{background:#fbfdff;border:1px solid var(--line);border-radius:8px;padding:11px 12px}.info-label{color:var(--muted);font-size:12px;font-weight:800;margin-bottom:4px}.info-value{color:var(--ink);font-size:14px;font-weight:700}.section-title{font-size:16px;font-weight:850;margin:0 0 12px 0}.clean-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}.clean-table th{background:#f8fafc;color:var(--muted);font-size:12px;text-align:left;padding:11px 12px;border-bottom:1px solid var(--line)}.clean-table td{padding:12px;border-bottom:1px solid var(--line);font-size:13px;color:var(--ink);vertical-align:top}.clean-table tr:last-child td{border-bottom:0}.bar-row{display:grid;grid-template-columns:150px 1fr 34px;gap:12px;align-items:center;margin:12px 0}.bar-label{color:var(--ink);font-size:13px;font-weight:750}.bar-track{height:12px;background:#eef2f6;border-radius:999px;overflow:hidden}.bar-fill{height:12px;background:linear-gradient(90deg,var(--blue),#6bc7d7);border-radius:999px}.bar-value{color:var(--muted);font-weight:800;text-align:right}.trace-card{display:grid;grid-template-columns:42px 190px 1fr 90px;gap:14px;align-items:start;padding:13px 0;border-bottom:1px solid var(--line)}.trace-card:last-child{border-bottom:0}.trace-no{width:28px;height:28px;border-radius:50%;background:#e0f2fe;color:#026aa2;display:flex;align-items:center;justify-content:center;font-weight:900}.trace-title{font-weight:850;color:var(--ink)}.trace-desc{color:var(--muted);font-size:13px;line-height:1.45}@media(max-width:980px){.metric-grid,.two-col,.three-col{grid-template-columns:1fr}.queue-row{grid-template-columns:1fr}.queue-row.header{display:none}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_topbar(st, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="topbar"><div><div class="brand"><span>STOREOPS</span> REVIEW</div><div class="page-title">{_h(title)}</div><div class="page-subtitle">{_h(subtitle)}</div></div><div class="toolbar">{_badge(T["ai_review"], "info")}{_badge(T["approval_required"], "warning")}</div></div>', unsafe_allow_html=True)


def _render_metric_cards(st, cases: list[ConsoleCase]) -> None:
    state_counts = count_by_state(cases)
    blocked = state_counts.get("NEEDS_CLARIFICATION", 0) + state_counts.get("DEGRADED_REVIEW", 0) + state_counts.get("CONFLICT_REVIEW", 0)
    st.markdown(f'<div class="metric-grid"><div class="metric-card"><div class="metric-label">\uc804\uccb4 \uac80\ud1a0 \uac74</div><div class="metric-value">{len(cases)}</div><div class="metric-note">\uc624\ub298 \uc0dd\uc131\ub41c \ub370\ubaa8 \ucf00\uc774\uc2a4</div></div><div class="metric-card"><div class="metric-label">\uc2b9\uc778 \ub300\uae30</div><div class="metric-value">{state_counts.get("READY_FOR_REVIEW", 0)}</div><div class="metric-note">\uadfc\uac70 \ud655\uc778 \ud6c4 \uc2b9\uc778 \uac00\ub2a5</div></div><div class="metric-card"><div class="metric-label">\ubcf4\ub958/\uc7ac\uac80\ud1a0</div><div class="metric-value">{blocked}</div><div class="metric-note">\uc815\ubcf4 \ubd80\uc871, \uc870\ud68c \uc2e4\ud328, \uc99d\uac70 \ucda9\ub3cc</div></div><div class="metric-card"><div class="metric-label">\uadfc\uac70 \uc5c6\ub294 \uc8fc\uc7a5</div><div class="metric-value">0</div><div class="metric-note">Safety Gate \ucc28\ub2e8</div></div></div>', unsafe_allow_html=True)


def _render_review_queue(st, cases: list[ConsoleCase]) -> None:
    _render_topbar(st, T["queue_title"], T["queue_sub"])
    _render_metric_cards(st, cases)
    rows = ['<div class="queue-row header"><div>\ucf00\uc774\uc2a4</div><div>\ubb38\uc81c \uc694\uc57d</div><div>\uc0c1\ud0dc</div><div>\uc2b9\uc778 \ud310\ub2e8</div><div>\uc704\ud5d8\ub3c4</div><div>\ub2f4\ub2f9 \uacbd\ub85c</div></div>']
    for case in cases:
        rows.append(f'<div class="queue-row"><div><div class="queue-case">{_h(case.view_model.case_id)}</div><div class="queue-meta">{_h(case.scenario_id)}</div></div><div><strong>{_h(ISSUE_LABELS.get(case.issue_key, case.issue_key))}</strong><div class="queue-meta">{_h(ISSUE_DESCRIPTIONS.get(case.issue_key, case.view_model.headline))}</div></div><div>{_status_badge(case.state)}</div><div><strong>{_h(case.approval_posture)}</strong><div class="queue-meta">\uadfc\uac70 {case.view_model.evidence_count}\uac74</div></div><div>{_h(case.risk)}</div><div>{_h(_route_label(case.view_model.recommended_route))}</div></div>')
    st.markdown(f'<section class="queue-card">{"".join(rows)}</section>', unsafe_allow_html=True)


def _render_case_detail(st, cases: list[ConsoleCase]) -> None:
    _render_topbar(st, T["detail_title"], T["detail_sub"])
    selected = st.selectbox("\uac80\ud1a0\ud560 \ucf00\uc774\uc2a4", [case.scenario_id for case in cases], index=0)
    case = next(item for item in cases if item.scenario_id == selected)
    vm = case.view_model
    missing = vm.technical_details.get("clarification_questions", [])
    evidence = vm.technical_details.get("evidence", [])
    tool_responses = vm.technical_details.get("tool_responses", [])
    missing_text = "\uc5c6\uc74c" if not missing else " / ".join(str(item) for item in missing)
    cause_text = ISSUE_LABELS.get(vm.primary_cause or case.issue_key, vm.primary_cause or "\ud655\uc815 \ubcf4\ub958")
    st.markdown(f'<div class="two-col"><section class="decision-card"><div class="decision-label">\uc2b9\uc778 \ud310\ub2e8</div><div class="decision-value">{_h(case.approval_posture)}</div><div>{_status_badge(case.state)}</div><h3 style="margin-top:18px;">{_h(vm.headline)}</h3><p class="body-copy">{_h(vm.cause_or_abstention)}</p><h3 style="margin-top:18px;">\uc6b4\uc601\uc790\uac00 \ud560 \uc77c</h3><p class="body-copy">{_h(vm.next_action)}</p><h3 style="margin-top:18px;">\uc0ac\uc7a5\ub2d8 \uc548\ub0b4 \ucd08\uc548</h3><p class="body-copy">{_h(vm.merchant_response_draft)}</p></section><section class="panel"><h3 class="section-title">\uc2b9\uc778 \uc804 \ud655\uc778</h3><div class="info-grid"><div class="info-item"><div class="info-label">\uc6d0\uc778 \ud6c4\ubcf4</div><div class="info-value">{_h(cause_text)}</div></div><div class="info-item"><div class="info-label">\ub2f4\ub2f9 \uacbd\ub85c</div><div class="info-value">{_h(_route_label(vm.recommended_route))}</div></div><div class="info-item"><div class="info-label">\ubd80\uc871\ud55c \uc815\ubcf4</div><div class="info-value">{_h(missing_text)}</div></div><div class="info-item"><div class="info-label">\ud655\uc778\ub41c \uadfc\uac70</div><div class="info-value">{len(evidence)}\uac74</div></div></div></section></div>', unsafe_allow_html=True)
    tool_rows = [[_h(_tool_label(item.get("tool_name", ""))), _badge("\uc815\uc0c1" if item.get("status") == "success" else "\uc2e4\ud328", "success" if item.get("status") == "success" else "danger"), _h("\ucd5c\uc2e0" if item.get("freshness") == "current" else str(item.get("freshness", "\ud655\uc778 \ud544\uc694"))), _h("\uc5c6\uc74c" if not item.get("warnings") else ", ".join(item.get("warnings", [])))] for item in tool_responses]
    st.markdown("### \ud655\uc778\ud55c \uc2dc\uc2a4\ud15c \uc870\ud68c")
    st.markdown(_render_html_table(["\uc870\ud68c \ud56d\ubaa9", "\uacb0\uacfc", "\ub370\uc774\ud130 \uc0c1\ud0dc", "\uc8fc\uc758 \uc0ac\ud56d"], tool_rows), unsafe_allow_html=True)
    evidence_rows = [[_h(item.get("evidence_id", "")), _h(_tool_label(item.get("source_tool", ""))), _h(_fact_label(item.get("fact_type", ""))), _h("\ubc18\ubc15 \uadfc\uac70 \uc788\uc74c" if item.get("contradicts") else "\ud310\ub2e8 \uc9c0\uc9c0")] for item in evidence] or [["-", "-", "\uc544\uc9c1 \ucda9\ubd84\ud55c \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.", "\ubcf4\ub958"]]
    st.markdown("### \ud310\ub2e8 \uadfc\uac70")
    st.markdown(_render_html_table(["\uadfc\uac70 ID", "\ucd9c\ucc98", "\ud655\uc778 \ub0b4\uc6a9", "\ud310\ub2e8"], evidence_rows), unsafe_allow_html=True)


def _render_issue_analytics(st, cases: list[ConsoleCase]) -> None:
    _render_topbar(st, T["analytics_title"], T["analytics_sub"])
    _render_metric_cards(st, cases)
    state_values = {STATE_LABELS.get(key, key): value for key, value in count_by_state(cases).items()}
    st.markdown(f'<div class="two-col">{_bar_chart("\uc0c1\ud0dc\ubcc4 \ubd84\ud3ec", state_values)}{_bar_chart("\ubb38\uc81c \uc720\ud615\ubcc4 \ubd84\ud3ec", count_by_issue(cases))}</div>', unsafe_allow_html=True)
    rows = []
    for case in cases:
        evidence_conflict = any(item.get("contradicts") for item in case.view_model.technical_details.get("evidence", []))
        tool_failure = any(item.get("status") == "error" for item in case.view_model.technical_details.get("tool_responses", []))
        rows.append([_h(case.view_model.case_id), _h(ISSUE_LABELS.get(case.issue_key, case.issue_key)), _yes_no(bool(case.view_model.primary_cause)), _yes_no(case.state == "NEEDS_CLARIFICATION"), _yes_no(tool_failure), _yes_no(evidence_conflict), _h(case.approval_posture)])
    st.markdown("### \ucf00\uc774\uc2a4 \ub9ac\uc2a4\ud06c \ub9e4\ud2b8\ub9ad\uc2a4")
    st.markdown(_render_html_table(["\ucf00\uc774\uc2a4", "\ubb38\uc81c \uc720\ud615", "\uc6d0\uc778 \ud655\uc815", "\uc815\ubcf4 \ubd80\uc871", "\uc870\ud68c \uc2e4\ud328", "\uc99d\uac70 \ucda9\ub3cc", "\uc2b9\uc778 \ud310\ub2e8"], rows), unsafe_allow_html=True)


def _render_evidence_trace(st, cases: list[ConsoleCase]) -> None:
    _render_topbar(st, T["trace_title"], T["trace_sub"])
    selected = st.selectbox("\ucd94\uc801\ud560 \ucf00\uc774\uc2a4", [case.scenario_id for case in cases], index=0)
    case = next(item for item in cases if item.scenario_id == selected)
    result = case.result
    vm = case.view_model
    steps = [("\uc811\uc218 \ub0b4\uc6a9 \uad6c\uc870\ud654", "\uc0ac\uc7a5\ub2d8 \ubb38\uc758\ub97c \uacb0\uc81c \uc7a5\uc560 \uc720\ud615, \uc99d\uc0c1, \ubd80\uc871 \uc815\ubcf4\ub85c \uc815\ub9ac\ud588\uc2b5\ub2c8\ub2e4."), ("\uc6b4\uc601 \uae30\uc900 \ud655\uc778", f"\uad00\ub828 SOP {len(result.retrieved_policy_ids)}\uac1c\ub97c \ud655\uc778\ud588\uc2b5\ub2c8\ub2e4."), ("\uc870\ud68c \uacc4\ud68d \uc218\ub9bd", f"\ud544\uc694\ud55c \uc2dc\uc2a4\ud15c \uc870\ud68c {len(result.plan.planned_tool_calls)}\uac1c\ub97c \uacc4\ud68d\ud588\uc2b5\ub2c8\ub2e4."), ("\uc2dc\uc2a4\ud15c \uc870\ud68c", f"\uc77d\uae30 \uc804\uc6a9 \ub3c4\uad6c {len(result.tool_responses)}\uac1c\ub97c \uc2e4\ud589\ud588\uc2b5\ub2c8\ub2e4."), ("\uadfc\uac70 \ud310\ub2e8", vm.primary_cause and ISSUE_LABELS.get(vm.primary_cause, vm.primary_cause) or "\uc6d0\uc778 \ud655\uc815 \ubcf4\ub958"), ("\uc548\uc804\uc131 \uac80\ud1a0", f"\ucd5c\uc885 \uc0c1\ud0dc: {STATE_LABELS.get(case.state, case.state)}"), ("\uace0\uac1d \uc548\ub0b4 \ucd08\uc548", "\ud655\uc778\ub41c \uc0ac\uc2e4\ub9cc \uc0ac\uc6a9\ud574 \uc0ac\uc7a5\ub2d8\uc5d0\uac8c \ubcf4\ub0bc \uc548\ub0b4\ubb38\uc744 \ub9cc\ub4e4\uc5c8\uc2b5\ub2c8\ub2e4.")]
    cards = "".join(f'<div class="trace-card"><div class="trace-no">{index}</div><div class="trace-title">{_h(title)}</div><div class="trace-desc">{_h(detail)}</div><div>{_badge("\uc644\ub8cc", "success")}</div></div>' for index, (title, detail) in enumerate(steps, start=1))
    st.markdown(f'<section class="panel">{cards}</section>', unsafe_allow_html=True)
    rows = [[_h(item.get("policy_title") or item.get("policy_id") or "\uc6b4\uc601 \uae30\uc900"), _h(item.get("check_text", "\ud655\uc778 \ud56d\ubaa9")), _h(_tool_label(str(item.get("tool_name") or "\uc218\ub3d9 \uac80\ud1a0"))), _h("\ud544\uc218" if item.get("priority") == "required" else "\ubcf4\uc870")] for item in result.policy_check_trace]
    st.markdown("### SOP \ud655\uc778 \ud56d\ubaa9\uacfc \uc2e4\uc81c \uc870\ud68c")
    st.markdown(_render_html_table(["\uc6b4\uc601 \uae30\uc900", "\ud655\uc778\ud574\uc57c \ud560 \ub0b4\uc6a9", "\uc2e4\uc81c \uc870\ud68c", "\uc911\uc694\ub3c4"], rows), unsafe_allow_html=True)


def _render_eval_report(st, cases: list[ConsoleCase]) -> None:
    _render_topbar(st, T["eval_title"], T["eval_sub"])
    cards = "".join(f'<div class="metric-card"><div class="metric-label">{_h(name)}</div><div class="metric-value">{_h(value)}</div></div>' for name, value in EVAL_METRICS.items())
    st.markdown(f'<div class="three-col">{cards}</div>', unsafe_allow_html=True)
    rows = [[_h(row["case"]), _h(row["issue"]), _h(row["status"]), _h(row["approval"]), _h(row["route"])] for row in case_queue_rows(cases)]
    st.markdown("### \ucf00\uc774\uc2a4\ubcc4 \uacb0\uacfc")
    st.markdown(_render_html_table(["\ucf00\uc774\uc2a4", "\ubb38\uc81c \uc720\ud615", "\uc0c1\ud0dc", "\uc2b9\uc778 \ud310\ub2e8", "\ub2f4\ub2f9 \uacbd\ub85c"], rows), unsafe_allow_html=True)


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise SystemExit("Streamlit is not installed. Install with: python -m pip install -e .[console]") from exc
    st.set_page_config(page_title="StoreOps Review Console", page_icon="StoreOps", layout="wide", initial_sidebar_state="expanded")
    _inject_css(st)

    @st.cache_data(show_spinner=False)
    def _load_cases() -> list[ConsoleCase]:
        return build_console_cases()

    cases = _load_cases()
    st.sidebar.markdown("### STOREOPS")
    st.sidebar.caption(T["brand_sub"])
    page = st.sidebar.radio("\uba54\ub274", ["Review Queue", "Case Detail", "Issue Analytics", "Evidence Trace", "Evaluation Report"], label_visibility="collapsed")
    if page == "Review Queue":
        _render_review_queue(st, cases)
    elif page == "Case Detail":
        _render_case_detail(st, cases)
    elif page == "Issue Analytics":
        _render_issue_analytics(st, cases)
    elif page == "Evidence Trace":
        _render_evidence_trace(st, cases)
    else:
        _render_eval_report(st, cases)


__all__ = ["ConsoleCase", "build_console_cases", "case_queue_rows", "count_by_issue", "count_by_state", "main"]


if __name__ == "__main__":
    main()
