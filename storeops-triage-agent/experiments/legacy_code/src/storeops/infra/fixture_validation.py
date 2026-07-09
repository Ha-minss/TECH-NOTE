"""Validation rules for synthetic fixtures."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


class FixtureValidationError(ValueError):
    """Raised when synthetic fixtures violate the data contract."""


@dataclass(frozen=True)
class FixtureValidationReport:
    valid: bool
    scenarios_checked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


OPERATIONAL_TABLES = (
    "stores",
    "terminals",
    "terminal_identities",
    "tid_assignments",
    "installation_events",
    "activation_events",
    "approval_events",
    "van_registrations",
    "pos_front_links",
    "pos_front_connection_events",
)

FORBIDDEN_COLUMNS = {"root_cause", "diagnosis", "expected_cause"}


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def validate_fixtures(
    connection: sqlite3.Connection,
    *,
    raise_on_error: bool = False,
) -> FixtureValidationReport:
    errors: list[str] = []

    for table in OPERATIONAL_TABLES:
        if not _table_exists(connection, table):
            errors.append(f"missing operational table: {table}")
            continue
        columns = {
            row["name"]
            for row in connection.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }
        leaked = FORBIDDEN_COLUMNS.intersection(columns)
        if leaked:
            errors.append(f"{table} leaks diagnosis columns: {sorted(leaked)}")

    if _table_exists(connection, "tid_assignments"):
        cross_store = connection.execute(
            """
            SELECT a.tid_assignment_id
            FROM tid_assignments a
            JOIN terminals t ON t.terminal_id = a.terminal_id
            WHERE a.store_id != t.store_id
            """
        ).fetchall()
        if cross_store:
            errors.append("cross-store terminal reference in tid_assignments")

        overlaps = connection.execute(
            """
            SELECT a.terminal_id
            FROM tid_assignments a
            JOIN tid_assignments b
              ON a.terminal_id = b.terminal_id
             AND a.tid_assignment_id < b.tid_assignment_id
             AND a.valid_from < COALESCE(b.valid_to, '9999-12-31')
             AND b.valid_from < COALESCE(a.valid_to, '9999-12-31')
            """
        ).fetchall()
        if overlaps:
            errors.append("overlapping TID assignments for one terminal")

    scenario_ids: list[str] = []
    if _table_exists(connection, "scenarios"):
        scenario_ids = [
            row["scenario_id"]
            for row in connection.execute(
                "SELECT scenario_id FROM scenarios ORDER BY scenario_id"
            ).fetchall()
        ]
    else:
        errors.append("missing scenario metadata table")

    report = FixtureValidationReport(
        valid=not errors,
        scenarios_checked=scenario_ids,
        errors=errors,
    )
    if errors and raise_on_error:
        raise FixtureValidationError("; ".join(errors))
    return report


__all__ = [
    "FixtureValidationError",
    "FixtureValidationReport",
    "validate_fixtures",
]
