"""Persist deterministic synthetic fixtures as SQLite and JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from storeops.domains.offline_payment_ops.scenario_runtime import seed_offline_payment_scenarios
from storeops.infra.database import create_database, seed_s1
from storeops.infra.fixture_validation import validate_fixtures


@dataclass(frozen=True)
class FixtureExport:
    sqlite_path: Path
    manifest_path: Path


def export_synthetic_fixtures(output_dir: Path) -> FixtureExport:
    output_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = output_dir / 'offline_payment_ops.sqlite3'
    manifest_path = output_dir / 'offline_payment_ops_manifest.json'
    if sqlite_path.exists():
        sqlite_path.unlink()

    connection = create_database(sqlite_path)
    try:
        seed_s1(connection)
        seed_offline_payment_scenarios(connection)
        report = validate_fixtures(connection)
        if not report.valid:
            raise ValueError(f'Fixture validation failed: {report.errors}')

        counts = {}
        tables = [
            row['name']
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        for table in tables:
            counts[table] = connection.execute(f'SELECT COUNT(*) AS count FROM {table}').fetchone()['count']
    finally:
        connection.close()

    manifest = {
        'fixture_version': 'offline-payment-ops-v1',
        'scenario_ids': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6A', 'S6B', 'S7'],
        'sqlite_file': sqlite_path.name,
        'table_counts': counts,
        'synthetic_only': True,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return FixtureExport(sqlite_path=sqlite_path, manifest_path=manifest_path)


__all__ = ['FixtureExport', 'export_synthetic_fixtures']

