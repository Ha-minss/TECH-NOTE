"""Run operator-facing scenario output."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import asdict

from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.operator.journeys import OperatorJourneyService


SCENARIOS = ("S1", "S2", "S3", "S4", "S5", "S6A", "S6B", "S7")
TID_PATTERN = re.compile(r"^(TID-)(.+)$")


def create_connection() -> sqlite3.Connection:
    connection = create_database()
    seed_s1(connection)
    seed_offline_payment_scenarios(connection)
    return connection


def run_view_model(scenario_id: str):
    connection = create_connection()
    try:
        service = OperatorJourneyService.default(connection)
        review = service.review_scenario(scenario_id)
        return review.view_model
    finally:
        connection.close()


def mask_sensitive(value: object) -> object:
    if isinstance(value, dict):
        return {key: mask_sensitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    if isinstance(value, str):
        match = TID_PATTERN.match(value)
        if match:
            return f"{match.group(1)}****{match.group(2)[-3:]}"
    return value


def run(scenario_id: str) -> dict:
    view_model = run_view_model(scenario_id)
    payload = asdict(view_model)
    payload["sections"] = [asdict(section) for section in view_model.sections]
    return mask_sensitive(payload)


def _configure_stdout() -> None:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_id", choices=SCENARIOS)
    args = parser.parse_args()
    print(json.dumps(run(args.scenario_id), ensure_ascii=False, indent=2))


__all__ = ["SCENARIOS", "create_connection", "mask_sensitive", "run", "run_view_model", "_configure_stdout"]


if __name__ == "__main__":
    main()

