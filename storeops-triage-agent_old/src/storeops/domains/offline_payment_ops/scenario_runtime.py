"""Synthetic S1-S7 fixtures and deterministic contract runner."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from storeops.core.contracts import (
    Assessment,
    CaseBrief,
    CaseState,
    CauseAssessment,
    EvidenceRecord,
    ToolError,
    ToolResponse,
    ToolStatus,
    WorkflowState,
)
from storeops.infra.tools import ToolGateway


EXTENDED_SCHEMA = """
CREATE TABLE IF NOT EXISTS terminal_identities (
    identity_record_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    terminal_id TEXT NOT NULL,
    registered_device_number TEXT NOT NULL,
    registered_serial TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    record_status TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    available_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS installation_events (
    installation_event_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    terminal_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    configuration_summary TEXT,
    observed_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    available_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS van_registrations (
    van_registration_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    merchant_number TEXT,
    registration_status TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    observed_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    available_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pos_front_links (
    link_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    pos_instance_id TEXT NOT NULL,
    front_terminal_id TEXT NOT NULL,
    pairing_status TEXT NOT NULL,
    network_segment TEXT,
    configured_front_ip TEXT,
    key_download_status TEXT,
    working_key_status TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pos_front_connection_events (
    connection_event_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    pos_instance_id TEXT NOT NULL,
    front_terminal_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    raw_code TEXT,
    raw_message TEXT,
    observed_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    available_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_failure_injections (
    failure_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    failure_mode TEXT NOT NULL,
    error_message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    merchant_message TEXT NOT NULL,
    expected_state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenario_stores (
    scenario_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL
);
"""


MESSAGES = {
    "S1": "어제 새 단말기를 설치했는데 오늘부터 기존 단말기에서 카드 승인이 안 돼요.",
    "S2": "새 단말기 들인 뒤로 기존 단말기에서 신용승인 오류가 떠요.",
    "S3": "단말기 설치는 됐는데 카드 승인할 때 가맹점 번호 미등록이라고 떠요.",
    "S4": "단말기는 켜져 있고 등록도 된 것 같은데, POS에서 결제 요청이 프론트로 제대로 안 넘어가요.",
    "S5": "새 단말기 설치했는데 결제가 안 돼요.",
    "S6A": "어제 새 단말기 설치했는데 오늘부터 기존 단말기에서 카드 승인이 안 돼요.",
    "S6B": "어제 새 단말기 설치했는데 오늘부터 기존 단말기에서 카드 승인이 안 돼요.",
    "S7": "새 단말기 설치 후 기존 단말기에서 카드 승인이 계속 실패해요.",
}


def _insert_many(
    connection: sqlite3.Connection,
    table: str,
    rows: Iterable[tuple[object, ...]],
) -> None:
    rows = list(rows)
    if not rows:
        return
    placeholders = ", ".join("?" for _ in rows[0])
    connection.executemany(
        f"INSERT INTO {table} VALUES ({placeholders})",
        rows,
    )


def _base_store_rows(scenario_ids: Iterable[str]) -> dict[str, list[tuple]]:
    stores = []
    access = []
    for scenario_id in scenario_ids:
        store_id = f"STR-{scenario_id}"
        stores.append(
            (store_id, f"합성 매장 {scenario_id}", "Asia/Seoul", "active")
        )
        access.append(("OP-DEMO", store_id, "review_case", 1))
    return {"stores": stores, "store_operator_access": access}


def seed_offline_payment_scenarios(connection: sqlite3.Connection) -> None:
    """Seed isolated, raw-fact fixtures for S1-S7 and S6 variants."""
    connection.executescript(EXTENDED_SCHEMA)
    scenario_ids = ("S2", "S3", "S4", "S5", "S6A", "S6B", "S7")
    base = _base_store_rows(scenario_ids)
    _insert_many(connection, "stores", base["stores"])
    _insert_many(
        connection,
        "store_operator_access",
        base["store_operator_access"],
    )

    _insert_many(connection, "scenarios", [
        ("S1", "새 단말기 설치 후 기존 단말기 승인 실패", MESSAGES["S1"], WorkflowState.READY_FOR_REVIEW.value),
        ("S2", "Terminal identity mismatch", MESSAGES["S2"], WorkflowState.READY_FOR_REVIEW.value),
        ("S3", "VAN merchant registration pending", MESSAGES["S3"], WorkflowState.READY_FOR_REVIEW.value),
        ("S4", "POS front connection issue", MESSAGES["S4"], WorkflowState.READY_FOR_REVIEW.value),
        ("S5", "Ambiguous payment failure", MESSAGES["S5"], WorkflowState.NEEDS_CLARIFICATION.value),
        ("S6A", "Duplicate TID with required tool failure", MESSAGES["S6A"], WorkflowState.DEGRADED_REVIEW.value),
        ("S6B", "Duplicate TID with optional route failure", MESSAGES["S6B"], WorkflowState.READY_FOR_REVIEW.value),
        ("S7", "Temporal TID conflict", MESSAGES["S7"], WorkflowState.CONFLICT_REVIEW.value),
    ])
    _insert_many(connection, "scenario_stores", [
        ("S1", "STR-S1"),
        ("S2", "STR-S2"),
        ("S3", "STR-S3"),
        ("S4", "STR-S4"),
        ("S5", "STR-S5"),
        ("S6A", "STR-S6A"),
        ("S6B", "STR-S6B"),
        ("S7", "STR-S7"),
    ])

    terminals = [
        ("TERM-S2-OLD", "STR-S2", "existing", "DEV-S2-ACTUAL", "SER-S2-ACTUAL", "activated", "2026-05-01T09:00:00+09:00", "2026-05-01T09:30:00+09:00"),
        ("TERM-S2-NEW", "STR-S2", "newly_installed", "DEV-S2-NEW", "SER-S2-NEW", "activated", "2026-06-20T14:30:00+09:00", "2026-06-20T15:00:00+09:00"),
        ("TERM-S3", "STR-S3", "newly_installed", "DEV-S3", "SER-S3", "activated", "2026-06-20T10:00:00+09:00", "2026-06-20T10:30:00+09:00"),
        ("TERM-S4", "STR-S4", "existing", "DEV-S4", "SER-S4", "activated", "2026-06-01T09:00:00+09:00", "2026-06-01T09:30:00+09:00"),
        ("TERM-S5-OLD", "STR-S5", "existing", "DEV-S5-OLD", "SER-S5-OLD", "activated", "2026-05-01T09:00:00+09:00", "2026-05-01T09:30:00+09:00"),
        ("TERM-S5-NEW", "STR-S5", "newly_installed", "DEV-S5-NEW", "SER-S5-NEW", "activated", "2026-06-20T14:30:00+09:00", "2026-06-20T15:00:00+09:00"),
        ("TERM-S6A-OLD", "STR-S6A", "existing", "DEV-S6A-OLD", "SER-S6A-OLD", "activated", "2026-05-01T09:00:00+09:00", "2026-05-01T09:30:00+09:00"),
        ("TERM-S6A-NEW", "STR-S6A", "newly_installed", "DEV-S6A-NEW", "SER-S6A-NEW", "activated", "2026-06-20T14:30:00+09:00", "2026-06-20T15:00:00+09:00"),
        ("TERM-S6B-OLD", "STR-S6B", "existing", "DEV-S6B-OLD", "SER-S6B-OLD", "activated", "2026-05-01T09:00:00+09:00", "2026-05-01T09:30:00+09:00"),
        ("TERM-S6B-NEW", "STR-S6B", "newly_installed", "DEV-S6B-NEW", "SER-S6B-NEW", "activated", "2026-06-20T14:30:00+09:00", "2026-06-20T15:00:00+09:00"),
        ("TERM-S7-OLD", "STR-S7", "existing", "DEV-S7-OLD", "SER-S7-OLD", "activated", "2026-05-01T09:00:00+09:00", "2026-05-01T09:30:00+09:00"),
        ("TERM-S7-NEW", "STR-S7", "newly_installed", "DEV-S7-NEW", "SER-S7-NEW", "activated", "2026-06-20T14:30:00+09:00", "2026-06-20T15:00:00+09:00"),
    ]
    _insert_many(connection, "terminals", terminals)

    identities = [
        ("IDENT-S2-OLD", "STR-S2", "TERM-S2-OLD", "DEV-S2-REGISTERED", "SER-S2-REGISTERED", "2026-05-01T09:00:00+09:00", None, "active", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("IDENT-S2-NEW", "STR-S2", "TERM-S2-NEW", "DEV-S2-NEW", "SER-S2-NEW", "2026-06-20T14:30:00+09:00", None, "active", "2026-06-20T14:30:00+09:00", "2026-06-20T14:30:01+09:00", "2026-06-20T14:30:02+09:00"),
        ("IDENT-S3", "STR-S3", "TERM-S3", "DEV-S3", "SER-S3", "2026-06-20T10:00:00+09:00", None, "active", "2026-06-20T10:00:00+09:00", "2026-06-20T10:00:01+09:00", "2026-06-20T10:00:02+09:00"),
        ("IDENT-S4", "STR-S4", "TERM-S4", "DEV-S4", "SER-S4", "2026-06-01T09:00:00+09:00", None, "active", "2026-06-01T09:00:00+09:00", "2026-06-01T09:00:01+09:00", "2026-06-01T09:00:02+09:00"),
    ]
    _insert_many(connection, "terminal_identities", identities)

    tid_rows = [
        ("TIDA-S2-OLD", "STR-S2", "TERM-S2-OLD", "TID-000201", "2026-05-01T09:30:00+09:00", None, "active", "2026-05-01T09:30:00+09:00", "2026-05-01T09:30:01+09:00", "2026-05-01T09:30:02+09:00"),
        ("TIDA-S2-NEW", "STR-S2", "TERM-S2-NEW", "TID-000202", "2026-06-20T15:00:00+09:00", None, "active", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("TIDA-S3", "STR-S3", "TERM-S3", "TID-000300", "2026-06-20T10:30:00+09:00", None, "active", "2026-06-20T10:30:00+09:00", "2026-06-20T10:30:01+09:00", "2026-06-20T10:30:02+09:00"),
        ("TIDA-S4", "STR-S4", "TERM-S4", "TID-000400", "2026-06-01T09:30:00+09:00", None, "active", "2026-06-01T09:30:00+09:00", "2026-06-01T09:30:01+09:00", "2026-06-01T09:30:02+09:00"),
        ("TIDA-S5-OLD", "STR-S5", "TERM-S5-OLD", "TID-000501", "2026-05-01T09:30:00+09:00", None, "active", "2026-05-01T09:30:00+09:00", "2026-05-01T09:30:01+09:00", "2026-05-01T09:30:02+09:00"),
        ("TIDA-S5-NEW", "STR-S5", "TERM-S5-NEW", "TID-000502", "2026-06-20T15:00:00+09:00", None, "active", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("TIDA-S6A-OLD", "STR-S6A", "TERM-S6A-OLD", "TID-000600", "2026-05-01T09:30:00+09:00", None, "active", "2026-05-01T09:30:00+09:00", "2026-05-01T09:30:01+09:00", "2026-05-01T09:30:02+09:00"),
        ("TIDA-S6A-NEW", "STR-S6A", "TERM-S6A-NEW", "TID-000600", "2026-06-20T15:00:00+09:00", None, "active", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("TIDA-S6B-OLD", "STR-S6B", "TERM-S6B-OLD", "TID-000610", "2026-05-01T09:30:00+09:00", None, "active", "2026-05-01T09:30:00+09:00", "2026-05-01T09:30:01+09:00", "2026-05-01T09:30:02+09:00"),
        ("TIDA-S6B-NEW", "STR-S6B", "TERM-S6B-NEW", "TID-000610", "2026-06-20T15:00:00+09:00", None, "active", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("TIDA-S7-OLD-H", "STR-S7", "TERM-S7-OLD", "TID-000700", "2026-05-01T09:30:00+09:00", None, "active", "2026-05-01T09:30:00+09:00", "2026-05-01T09:30:01+09:00", "2026-05-01T09:30:02+09:00"),
        ("TIDA-S7-NEW-H", "STR-S7", "TERM-S7-NEW", "TID-000700", "2026-06-20T15:00:00+09:00", "2026-06-20T16:10:00+09:00", "replaced", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("TIDA-S7-NEW-C", "STR-S7", "TERM-S7-NEW", "TID-000701", "2026-06-20T16:10:00+09:00", None, "active", "2026-06-20T16:10:00+09:00", "2026-06-20T16:10:01+09:00", "2026-06-20T16:10:02+09:00"),
    ]
    _insert_many(connection, "tid_assignments", tid_rows)

    activation_rows = [
        ("ACT-S6A", "STR-S6A", "TERM-S6A-NEW", "terminal_open", "succeeded", "TID-000600", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("ACT-S6B", "STR-S6B", "TERM-S6B-NEW", "terminal_open", "succeeded", "TID-000610", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
        ("ACT-S7", "STR-S7", "TERM-S7-NEW", "terminal_open", "succeeded", "TID-000700", "2026-06-20T15:00:00+09:00", "2026-06-20T15:00:01+09:00", "2026-06-20T15:00:02+09:00"),
    ]
    _insert_many(connection, "activation_events", activation_rows)

    approval_rows = [
        ("APR-S2", "STR-S2", "TERM-S2-OLD", "transport_error", "card_terminal", "SYN-ID-01", "단말기 식별 정보 확인 필요", "2026-06-20T15:08:00+09:00", "2026-06-20T15:08:01+09:00", "2026-06-20T15:08:02+09:00"),
        ("APR-S3", "STR-S3", "TERM-S3", "declined", "card_terminal", "SYN-MERCHANT-01", "신용 승인 가맹점 번호 미등록", "2026-06-20T10:35:00+09:00", "2026-06-20T10:35:01+09:00", "2026-06-20T10:35:02+09:00"),
        ("APR-S6A", "STR-S6A", "TERM-S6A-OLD", "transport_error", "card_terminal", "SYN-GENERIC-01", "신용승인 처리 실패", "2026-06-20T15:07:00+09:00", "2026-06-20T15:07:01+09:00", "2026-06-20T15:07:02+09:00"),
        ("APR-S6B", "STR-S6B", "TERM-S6B-OLD", "transport_error", "card_terminal", "SYN-GENERIC-01", "신용승인 처리 실패", "2026-06-20T15:07:00+09:00", "2026-06-20T15:07:01+09:00", "2026-06-20T15:07:02+09:00"),
        ("APR-S7", "STR-S7", "TERM-S7-OLD", "transport_error", "card_terminal", "SYN-GENERIC-01", "신용승인 처리 실패", "2026-06-20T15:20:00+09:00", "2026-06-20T15:20:01+09:00", "2026-06-20T15:20:02+09:00"),
    ]
    _insert_many(connection, "approval_events", approval_rows)

    installation_rows = [
        ("INST-S2", "STR-S2", "TERM-S2-NEW", "installed", '{"source":"synthetic"}', "2026-06-20T14:30:00+09:00", "2026-06-20T14:31:00+09:00", "2026-06-20T14:31:01+09:00"),
        ("INST-S7", "STR-S7", "TERM-S7-NEW", "configured", '{"history":"incomplete"}', "2026-06-20T16:10:00+09:00", "2026-06-20T16:11:00+09:00", "2026-06-20T16:11:01+09:00"),
    ]
    _insert_many(connection, "installation_events", installation_rows)

    van_rows = [
        ("VAN-S3", "STR-S3", None, "pending", "2026-06-20T10:00:00+09:00", None, "2026-06-20T10:00:00+09:00", "2026-06-20T10:00:01+09:00", "2026-06-20T10:00:02+09:00"),
        ("VAN-S4", "STR-S4", "MERCHANT-S4", "active", "2026-06-01T09:00:00+09:00", None, "2026-06-01T09:00:00+09:00", "2026-06-01T09:00:01+09:00", "2026-06-01T09:00:02+09:00"),
    ]
    _insert_many(connection, "van_registrations", van_rows)

    pos_links = [
        ("LINK-S4", "STR-S4", "POS-S4", "TERM-S4", "disconnected", "NET-A", "192.0.2.10", "current", "valid", "2026-06-20T15:00:00+09:00"),
    ]
    _insert_many(connection, "pos_front_links", pos_links)
    pos_events = [
        ("CONN-S4", "STR-S4", "POS-S4", "TERM-S4", "request_failed", "timeout", "SYN-CONN-01", "프론트 요청 전달 시간 초과", "2026-06-20T15:05:00+09:00", "2026-06-20T15:05:01+09:00", "2026-06-20T15:05:02+09:00"),
    ]
    _insert_many(connection, "pos_front_connection_events", pos_events)

    routes = [
        ("ROUTE-S2", "STR-S2", "terminal_identifier_mismatch", "installation_partner", "합성 설치 지원", "active"),
        ("ROUTE-S3", "STR-S3", "van_merchant_registration_missing", "van_agency", "합성 VAN 등록 지원", "active"),
        ("ROUTE-S4", "STR-S4", "pos_front_connection_issue", "pos_front_support", "합성 POS–Front 지원", "active"),
    ]
    _insert_many(connection, "support_routes", routes)

    failures = [
        ("FAIL-S6A", "S6A", "get_tid_config", "timeout", "TID registry timed out."),
        ("FAIL-S6B", "S6B", "get_support_route", "unavailable", "Support directory unavailable."),
    ]
    _insert_many(connection, "tool_failure_injections", failures)
    connection.commit()


class OfflinePaymentScenarioGateway(ToolGateway):
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        scenario_id: str,
        operator_id: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            connection,
            operator_id=operator_id,
            trace_id=trace_id,
        )
        self.scenario_id = scenario_id

    def _failure(self, tool_name: str, store_id: str) -> ToolResponse | None:
        row = self.connection.execute(
            """
            SELECT * FROM tool_failure_injections
            WHERE scenario_id = ? AND tool_name = ?
            """,
            (self.scenario_id, tool_name),
        ).fetchone()
        if row is None:
            return None
        error_type = {
            "timeout": "ToolTimeoutError",
            "unavailable": "ToolUnavailableError",
        }.get(row["failure_mode"], "ToolUnavailableError")
        return ToolResponse(
            tool_name=tool_name,
            trace_id=self.trace_id,
            store_id=store_id,
            status=ToolStatus.ERROR,
            error=ToolError(
                error_type=error_type,
                message=row["error_message"],
            ),
        )

    def get_tid_config(self, store_id: str) -> ToolResponse:
        failure = self._failure("get_tid_config", store_id)
        return failure or super().get_tid_config(store_id)

    def get_support_route(self, store_id: str, issue_type: str) -> ToolResponse:
        failure = self._failure("get_support_route", store_id)
        return failure or super().get_support_route(store_id, issue_type)

    def get_terminal_identity(self, store_id: str) -> ToolResponse:
        return self._query(
            tool_name="get_terminal_identity",
            store_id=store_id,
            sql="""
                SELECT t.terminal_id, t.device_number, t.physical_serial,
                       i.identity_record_id, i.registered_device_number,
                       i.registered_serial, i.observed_at, i.recorded_at, i.available_at
                FROM terminals t
                JOIN terminal_identities i ON i.terminal_id = t.terminal_id
                WHERE t.store_id = ? AND i.valid_to IS NULL
                ORDER BY t.terminal_id
            """,
            params=(store_id,),
        )

    def get_installation_history(self, store_id: str) -> ToolResponse:
        return self._query(
            tool_name="get_installation_history",
            store_id=store_id,
            sql="""
                SELECT * FROM installation_events
                WHERE store_id = ? ORDER BY observed_at
            """,
            params=(store_id,),
        )

    def get_van_registration(self, store_id: str) -> ToolResponse:
        return self._query(
            tool_name="get_van_registration",
            store_id=store_id,
            sql="""
                SELECT * FROM van_registrations
                WHERE store_id = ? AND valid_to IS NULL
                ORDER BY observed_at
            """,
            params=(store_id,),
        )

    def get_pos_front_connection_logs(self, store_id: str) -> ToolResponse:
        return self._query(
            tool_name="get_pos_front_connection_logs",
            store_id=store_id,
            sql="""
                SELECT 'snapshot' AS record_type, link_id AS record_id,
                       pairing_status AS status, updated_at AS observed_at
                FROM pos_front_links WHERE store_id = ?
                UNION ALL
                SELECT 'event', connection_event_id, event_status, observed_at
                FROM pos_front_connection_events WHERE store_id = ?
                ORDER BY observed_at
            """,
            params=(store_id, store_id),
        )

    def get_tid_history(self, store_id: str) -> ToolResponse:
        return self._query(
            tool_name="get_tid_history",
            store_id=store_id,
            sql="""
                SELECT * FROM tid_assignments
                WHERE store_id = ? ORDER BY valid_from
            """,
            params=(store_id,),
        )


def _state(scenario_id: str, trace_id: str) -> CaseState:
    now = datetime.fromisoformat("2026-06-20T17:00:00+09:00")
    return CaseState(
        case_id=f"CASE-{scenario_id}",
        trace_id=trace_id,
        scenario_id=scenario_id,
        store_id=f"STR-{scenario_id}",
        merchant_message=MESSAGES[scenario_id],
        created_at=now,
        updated_at=now,
    )


def _evidence(
    scenario_id: str,
    source_tool: str,
    source_record_id: str,
    fact_type: str,
    value: object,
    observed_at: str,
    *,
    supports: list[str] | None = None,
    contradicts: list[str] | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"EV-{scenario_id}-{fact_type.upper()}",
        source_tool=source_tool,
        source_record_id=source_record_id,
        fact_type=fact_type,
        normalized_value=value,
        observed_at=datetime.fromisoformat(observed_at),
        supports=supports or [],
        contradicts=contradicts or [],
    )


def _brief(
    state: CaseState,
    *,
    cause: str | None,
    assessment: Assessment,
    evidence: list[EvidenceRecord] | None = None,
    alternatives: list[str] | None = None,
    missing: list[str] | None = None,
    checks: list[str] | None = None,
    route: str | None = None,
    actions: list[str],
    response: str,
) -> tuple[CaseState, CaseBrief]:
    evidence = evidence or []
    state.evidence.extend(evidence)
    return state, CaseBrief(
        cause=CauseAssessment(
            primary_cause=cause,
            assessment=assessment,
            supporting_evidence_ids=[
                record.evidence_id for record in evidence if record.supports
            ],
            contradicting_evidence_ids=[
                record.evidence_id for record in evidence if record.contradicts
            ],
            alternative_causes=alternatives or [],
            missing_evidence=missing or [],
            next_checks=checks or [],
            forbidden_actions=[
                "change_tid_without_confirmation",
                "execute_payment",
                "modify_registration",
            ],
        ),
        state=state.current_state,
        operator_actions=actions,
        recommended_route=route,
        merchant_response=response,
    )


def _route(
    gateway: OfflinePaymentScenarioGateway,
    state: CaseState,
    cause: str,
) -> str | None:
    response = gateway.get_support_route(state.store_id, cause)
    state.tool_calls.append(response.tool_name)
    if response.status is ToolStatus.SUCCESS:
        return str(response.data[0]["destination_label"])
    return None


def _run_s2(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    tids = gateway.get_tid_config(state.store_id)
    identities = gateway.get_terminal_identity(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend(
        [tids.tool_name, identities.tool_name, errors.tool_name]
    )
    tid_values = [row["tid"] for row in tids.data]
    mismatches = [
        row
        for row in identities.data
        if row["device_number"] != row["registered_device_number"]
        or row["physical_serial"] != row["registered_serial"]
    ]
    if len(set(tid_values)) == len(tid_values) and mismatches and errors.data:
        state.current_state = WorkflowState.READY_FOR_REVIEW
        ev = _evidence(
            "S2",
            "get_terminal_identity",
            mismatches[0]["identity_record_id"],
            "terminal_identity_mismatch",
            {
                "terminal_id": mismatches[0]["terminal_id"],
                "device_number_matches": False,
                "serial_matches": False,
            },
            mismatches[0]["observed_at"],
            supports=["terminal_identifier_mismatch"],
        )
        return _brief(
            state,
            cause="terminal_identifier_mismatch",
            assessment=Assessment.LIKELY,
            evidence=[ev],
            route=_route(gateway, state, "terminal_identifier_mismatch"),
            actions=["실물 단말기 번호와 등록된 식별값을 대조합니다."],
            response="단말기 식별 정보가 등록값과 달라 설치 담당자가 확인합니다.",
        )
    raise AssertionError("S2 fixture does not satisfy its contract")


def _run_s3(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    tids = gateway.get_tid_config(state.store_id)
    identities = gateway.get_terminal_identity(state.store_id)
    van = gateway.get_van_registration(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend(
        [tids.tool_name, identities.tool_name, van.tool_name, errors.tool_name]
    )
    incomplete = [
        row for row in van.data if row["registration_status"] != "active"
    ]
    if tids.data and identities.data and incomplete and errors.data:
        state.current_state = WorkflowState.READY_FOR_REVIEW
        ev = _evidence(
            "S3",
            "get_van_registration",
            incomplete[0]["van_registration_id"],
            "van_registration_incomplete",
            {"status": incomplete[0]["registration_status"]},
            incomplete[0]["observed_at"],
            supports=["van_merchant_registration_missing"],
        )
        return _brief(
            state,
            cause="van_merchant_registration_missing",
            assessment=Assessment.LIKELY,
            evidence=[ev],
            route=_route(
                gateway,
                state,
                "van_merchant_registration_missing",
            ),
            actions=["VAN 가맹점 등록 상태를 확인합니다."],
            response="가맹점 등록이 완료되지 않아 VAN 등록 담당자가 확인합니다.",
        )
    raise AssertionError("S3 fixture does not satisfy its contract")


def _run_s4(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    connection = gateway.get_pos_front_connection_logs(state.store_id)
    state.tool_calls.append(connection.tool_name)
    abnormal = [
        row
        for row in connection.data
        if row["status"] in {"disconnected", "failed", "timeout", "mismatch"}
    ]
    if abnormal:
        state.current_state = WorkflowState.READY_FOR_REVIEW
        ev = _evidence(
            "S4",
            connection.tool_name,
            ",".join(str(row["record_id"]) for row in abnormal),
            "pos_front_request_delivery_failure",
            {"statuses": [row["status"] for row in abnormal]},
            abnormal[0]["observed_at"],
            supports=["pos_front_connection_issue"],
        )
        return _brief(
            state,
            cause="pos_front_connection_issue",
            assessment=Assessment.LIKELY,
            evidence=[ev],
            route=_route(gateway, state, "pos_front_connection_issue"),
            actions=["POS–Front 네트워크와 연결 상태를 확인합니다."],
            response="POS와 프론트 사이 요청 전달 상태를 담당자가 확인합니다.",
        )
    raise AssertionError("S4 fixture does not satisfy its contract")


def _run_s5(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    store_info = gateway.get_store_info(state.store_id)
    terminals = gateway.get_terminals(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend([store_info.tool_name, terminals.tool_name, errors.tool_name])
    state.current_state = WorkflowState.NEEDS_CLARIFICATION
    return _brief(
        state,
        cause=None,
        assessment=Assessment.UNAVAILABLE,
        missing=["failed_physical_terminal", "visible_error_message"],
        actions=[
            "기존 단말기와 새 단말기 중 어느 기기에서 오류가 발생하나요?",
            "화면에 표시되는 오류 문구가 무엇인가요?",
        ],
        response="시스템에서 확인할 수 없는 두 가지 정보만 추가로 확인하겠습니다.",
    )


def _duplicate_tid_evidence(
    gateway: OfflinePaymentScenarioGateway,
    state: CaseState,
) -> list[EvidenceRecord] | None:
    tids = gateway.get_tid_config(state.store_id)
    state.tool_calls.append(tids.tool_name)
    if tids.status is not ToolStatus.SUCCESS:
        return None
    groups: dict[str, list[dict]] = {}
    for row in tids.data:
        groups.setdefault(str(row["tid"]), []).append(row)
    duplicate = next((rows for rows in groups.values() if len(rows) > 1), None)
    if duplicate is None:
        return []
    return [
        _evidence(
            state.scenario_id,
            tids.tool_name,
            ",".join(row["tid_assignment_id"] for row in duplicate),
            "duplicate_tid_assignment",
            {"terminal_ids": [row["terminal_id"] for row in duplicate]},
            duplicate[-1]["observed_at"],
            supports=["duplicate_tid"],
        )
    ]


def _run_s6a(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    activations = gateway.get_activation_history(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend([activations.tool_name, errors.tool_name])
    evidence = _duplicate_tid_evidence(gateway, state)
    if evidence is None:
        state.current_state = WorkflowState.DEGRADED_REVIEW
        return _brief(
            state,
            cause=None,
            assessment=Assessment.UNAVAILABLE,
            missing=["get_tid_config"],
            actions=["필수 TID 설정을 수동으로 확인합니다."],
            response="필수 설정 조회가 실패해 제한된 검토로 전환했습니다.",
        )
    raise AssertionError("S6A must inject required Tool failure")


def _run_s6b(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    terminals = gateway.get_terminals(state.store_id)
    activations = gateway.get_activation_history(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend([terminals.tool_name, activations.tool_name, errors.tool_name])
    evidence = _duplicate_tid_evidence(gateway, state)
    if not evidence:
        raise AssertionError("S6B requires duplicate TID evidence")
    state.current_state = WorkflowState.READY_FOR_REVIEW
    route = _route(gateway, state, "duplicate_tid")
    return _brief(
        state,
        cause="duplicate_tid",
        assessment=Assessment.LIKELY,
        evidence=evidence,
        route=route,
        actions=["원인 검토 후 담당 경로를 운영자가 직접 선택합니다."],
        response="동일 TID 가능성은 확인됐지만 전달 경로는 운영자가 선택합니다.",
    )


def _run_s7(gateway: OfflinePaymentScenarioGateway, state: CaseState):
    current = gateway.get_tid_config(state.store_id)
    history = gateway.get_tid_history(state.store_id)
    activations = gateway.get_activation_history(state.store_id)
    errors = gateway.get_recent_approval_errors(state.store_id)
    state.tool_calls.extend(
        [
            current.tool_name,
            history.tool_name,
            activations.tool_name,
            errors.tool_name,
        ]
    )
    current_tids = {row["tid"] for row in current.data}
    incident_time = datetime.fromisoformat("2026-06-20T15:20:00+09:00")
    incident_rows = [
        row
        for row in history.data
        if datetime.fromisoformat(row["valid_from"]) <= incident_time
        and (
            row["valid_to"] is None
            or incident_time < datetime.fromisoformat(row["valid_to"])
        )
    ]
    incident_tids = [row["tid"] for row in incident_rows]
    conflict = len(current_tids) > 1 and len(set(incident_tids)) < len(incident_tids)
    if conflict and activations.data and errors.data:
        state.current_state = WorkflowState.CONFLICT_REVIEW
        ev_current = _evidence(
            "S7",
            current.tool_name,
            ",".join(row["tid_assignment_id"] for row in current.data),
            "current_tid_configuration",
            {"distinct": True},
            current.data[-1]["observed_at"],
            contradicts=["temporary_duplicate_tid"],
        )
        ev_history = _evidence(
            "S7",
            history.tool_name,
            ",".join(row["tid_assignment_id"] for row in incident_rows),
            "incident_time_tid_configuration",
            {"duplicate_at_incident": True},
            incident_rows[-1]["observed_at"],
            supports=["temporary_duplicate_tid"],
        )
        return _brief(
            state,
            cause=None,
            assessment=Assessment.NEEDS_CONFIRMATION,
            evidence=[ev_current, ev_history],
            alternatives=[
                "temporary_duplicate_tid",
                "post_incident_configuration_change",
                "incomplete_activation_history",
            ],
            checks=[
                "inspect_incident_time_tid_history",
                "confirm_activation_sequence",
                "confirm_historical_van_registration_if_needed",
            ],
            actions=["사건 당시 설정과 현재 설정을 시간순으로 검증합니다."],
            response="현재 설정과 사건 당시 기록이 달라 단일 원인으로 확정하지 않습니다.",
        )
    raise AssertionError("S7 fixture does not create temporal conflict")


RUNNERS = {
    "S2": _run_s2,
    "S3": _run_s3,
    "S4": _run_s4,
    "S5": _run_s5,
    "S6A": _run_s6a,
    "S6B": _run_s6b,
    "S7": _run_s7,
}


def run_scenario(
    connection: sqlite3.Connection,
    scenario_id: str,
    *,
    operator_id: str,
    trace_id: str,
) -> tuple[CaseState, CaseBrief]:
    try:
        runner = RUNNERS[scenario_id]
    except KeyError as error:
        raise ValueError(f"Unsupported scenario: {scenario_id}") from error
    state = _state(scenario_id, trace_id)
    gateway = OfflinePaymentScenarioGateway(
        connection,
        scenario_id=scenario_id,
        operator_id=operator_id,
        trace_id=trace_id,
    )
    return runner(gateway, state)


ScenarioGateway = OfflinePaymentScenarioGateway
seed_all_scenarios = seed_offline_payment_scenarios

__all__ = ['EXTENDED_SCHEMA', 'MESSAGES', 'OfflinePaymentScenarioGateway', 'ScenarioGateway', 'run_scenario', 'seed_offline_payment_scenarios', 'seed_all_scenarios']
