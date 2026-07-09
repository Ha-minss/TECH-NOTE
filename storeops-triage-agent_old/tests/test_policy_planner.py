import json
import unittest
from pathlib import Path

from storeops.core.planner import (
    DataNeedPriority,
    Planner,
    PlannerOutput,
    ToolCatalog,
)
from storeops.core.retrieval import DeterministicEmbeddingProvider, HybridPolicyRetriever


class PolicyPlannerTests(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.policy_dir = self.project_root / "data" / "policies" / "offline_payment_ops"
        self.catalog_path = self.project_root / "data" / "tool_catalog" / "offline_payment_ops_tools.json"
        self.planner_cases_path = self.project_root / "data" / "evaluation" / "planner_cases.json"

    def test_tool_catalog_loads_read_only_capabilities_by_data_need(self):
        catalog = ToolCatalog.load(self.catalog_path)

        self.assertEqual(catalog.tool_for_data_need("terminal_inventory").tool_name, "get_terminals")
        self.assertEqual(catalog.tool_for_data_need("approval_failure_history").tool_name, "get_recent_approval_errors")
        self.assertTrue(all(tool.read_only for tool in catalog.tools))

    def test_planner_output_schema_preserves_reasons_and_tool_calls(self):
        output = PlannerOutput(
            case_type="ambiguous_payment_failure",
            data_needs=[
                {
                    "name": "approval_failure_history",
                    "priority": DataNeedPriority.REQUIRED,
                    "reason": "승인 실패 내역 확인이 필요함",
                }
            ],
            planned_tool_calls=[
                {
                    "tool_name": "get_recent_approval_errors",
                    "data_need": "approval_failure_history",
                    "reason": "승인 실패 내역 확인이 필요함",
                    "required": True,
                }
            ],
            clarification_candidates=["visible_error_message"],
            forbidden_actions=["payment_execution"],
            retrieved_policy_ids=["SOP-PAY-OP-001"],
        )

        self.assertEqual(output.data_needs[0].name, "approval_failure_history")
        self.assertTrue(output.planned_tool_calls[0].required)

    def test_planner_golden_cases_select_required_data_needs_and_avoid_forbidden_tools(self):
        catalog = ToolCatalog.load(self.catalog_path)
        retriever = HybridPolicyRetriever.from_policy_dir(
            self.policy_dir,
            embedding_provider=DeterministicEmbeddingProvider(),
            dense_weight=0.6,
            bm25_weight=0.4,
        )
        planner = Planner(tool_catalog=catalog)
        cases = json.loads(self.planner_cases_path.read_text(encoding="utf-8"))

        failures = []
        for case in cases:
            retrieved = retriever.search(case["query"], top_k=case["top_k"])
            plan = planner.plan(query=case["query"], retrieved_policies=retrieved)
            data_needs = {need.name for need in plan.data_needs}
            tool_names = {call.tool_name for call in plan.planned_tool_calls}
            missing_needs = sorted(set(case["required_data_needs"]) - data_needs)
            forbidden_needs = sorted(set(case["forbidden_data_needs"]) & data_needs)
            forbidden_tools = sorted(set(case["forbidden_tool_names"]) & tool_names)
            missing_clarifications = sorted(
                set(case.get("required_clarification_candidates", []))
                - set(plan.clarification_candidates)
            )
            if missing_needs or forbidden_needs or forbidden_tools or missing_clarifications:
                failures.append(
                    {
                        "case_id": case["case_id"],
                        "missing_needs": missing_needs,
                        "forbidden_needs": forbidden_needs,
                        "forbidden_tools": forbidden_tools,
                        "missing_clarifications": missing_clarifications,
                        "planned_needs": sorted(data_needs),
                        "planned_tools": sorted(tool_names),
                    }
                )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
