"""Run the LLM-assisted portfolio demo flow."""

from __future__ import annotations

import argparse
import json
import sys

from storeops.apps.operator_cli import SCENARIOS
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.infra.database import create_database, seed_s1
from storeops.evals.datasets import load_golden_cases
from storeops.evals.llm_runner import build_scripted_client
from storeops.llm.providers.live import LiveLLMClient
from storeops.operator.view_model import OperatorCaseViewModel


def _default_scripted_client(scenario_id: str):
    cases = [case for case in load_golden_cases() if case.fixture_key == scenario_id]
    if not cases:
        raise ValueError(f"No scripted demo case for scenario: {scenario_id}")
    return build_scripted_client(cases)


def _serialize_llm_traces(traces) -> list[dict[str, object]]:
    return [
        {
            "prompt_name": trace.prompt_name,
            "model_name": trace.model_name,
            "status": trace.status,
            "latency_ms": trace.latency_ms,
            "used_fallback": trace.used_fallback,
            "error_message": trace.error_message,
        }
        for trace in traces
    ]


def run_demo_case(
    scenario_id: str,
    *,
    client=None,
    model_name: str = "scripted-demo",
) -> dict:
    connection = create_database()
    seed_s1(connection)
    seed_offline_payment_scenarios(connection)
    try:
        actual_client = client or _default_scripted_client(scenario_id)
        workflow = OfflinePaymentWorkflow.with_llm(
            connection,
            client=actual_client,
            model_name=model_name,
        )
        result = workflow.run_scenario(
            scenario_id,
            operator_id="OP-DEMO",
            trace_id=f"TRACE-LLM-DEMO-{scenario_id}",
        )
        view_model = OperatorCaseViewModel.from_workflow_result(result)
        provider = "custom-client" if client is not None else "scripted-demo"
        return {
            "scenario_id": scenario_id,
            "provider": provider,
            "model_name": model_name,
            "state": result.state.current_state.value,
            "clarification_questions": list(result.clarification_questions),
            "merchant_response": view_model.merchant_response_draft,
            "headline": view_model.headline,
            "planned_tools": [call.tool_name for call in result.plan.planned_tool_calls],
            "llm_traces": _serialize_llm_traces(getattr(result, "llm_traces", [])),
        }
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_id", choices=SCENARIOS)
    parser.add_argument(
        "--provider",
        choices=["scripted", "scripted-demo", "live"],
        default="scripted-demo",
    )
    parser.add_argument("--config", default="config/live.local.json")
    parser.add_argument("--model", default="scripted-demo")
    args = parser.parse_args(argv)

    if args.provider == "live":
        client = LiveLLMClient.from_sources(config_path=args.config)
        provider = "live"
    else:
        client = _default_scripted_client(args.scenario_id)
        provider = "scripted-demo"

    payload = run_demo_case(args.scenario_id, client=client, model_name=args.model)
    payload["provider"] = provider
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["run_demo_case"]


if __name__ == "__main__":
    main()

