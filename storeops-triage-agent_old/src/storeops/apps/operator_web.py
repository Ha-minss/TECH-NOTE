"""Export a standalone HTML operator demo page for a scenario."""

from __future__ import annotations

from pathlib import Path

from storeops.apps.operator_cli import run_view_model
from storeops.operator.web_ui import render_operator_case_html


def build_html(scenario_id: str) -> str:
    return render_operator_case_html(run_view_model(scenario_id))


def export_html(scenario_id: str, output_path: str | Path) -> str:
    html = build_html(scenario_id)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return html


__all__ = ["build_html", "export_html"]
