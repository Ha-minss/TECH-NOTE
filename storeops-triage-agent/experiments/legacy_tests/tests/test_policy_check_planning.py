import sqlite3
import unittest
from pathlib import Path

from storeops.apps.operator_cli import create_connection
from storeops.core.planner import ToolCatalog
from storeops.core.policy_checks import EvidencePlanBuilder, PolicyCheck
from storeops.domains.offline_payment_ops.workflow import build_offline_payment_workflow


class PolicyChecklistPlanningTests(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.catalog = ToolCatalog.load(
            self.project_root / "data" / "tool_catalog" / "offline_payment_ops_tools.json"
        )

    def test_evidence_plan_builder_maps_policy_checks_to_existing_tools_and_merges_duplicates(self):
        checks = [
            PolicyCheck(
                policy_id="SOP-PAY-OP-003",
                policy_title="VAN registration checks",
                check_text="Check terminal payment identifier settings.",
                matched_data_need="payment_identifier_config",
                priority="required",
                reason="SOP check matches tool catalog payment identifier config.",
                source_quote="terminal payment identifier settings",
            ),
            PolicyCheck(
                policy_id="SOP-PAY-OP-003",
                policy_title="VAN registration checks",
                check_text="Check terminal payment identifier settings again.",
                matched_data_need="payment_identifier_config",
                priority="supporting",
                reason="Duplicate SOP check should not execute the same tool twice.",
                source_quote="payment identifier settings",
            ),
            PolicyCheck(
                policy_id="SOP-PAY-OP-003",
                policy_title="VAN registration checks",
                check_text="Check a policy item that has no safe tool mapping.",
                matched_data_need=None,
                priority="optional",
                reason="No catalog data_need matched clearly.",
            ),
        ]

        plan, trace = EvidencePlanBuilder().build(
            policy_checks=checks,
            tool_catalog=self.catalog,
            retrieved_policy_ids=["SOP-PAY-OP-003"],
        )

        self.assertEqual([call.tool_name for call in plan.planned_tool_calls], ["get_tid_config"])
        self.assertTrue(plan.planned_tool_calls[0].required)
        self.assertEqual(plan.data_needs[0].name, "payment_identifier_config")
        self.assertEqual(len(trace), 3)
        self.assertEqual(trace[0]["tool_name"], "get_tid_config")
        self.assertEqual(trace[0]["source"], "checklist_extractor")
        self.assertEqual(trace[2]["source"], "unmatched_policy_check")

    def test_core_workflow_source_has_no_legacy_planner_path(self):
        workflow_source = (self.project_root / "src" / "storeops" / "core" / "workflow.py").read_text(encoding="utf-8")

        for banned in (
            "legacy_plan",
            "merge_with_legacy_plan",
            "self.planner.plan",
            "planner.tool_catalog",
        ):
            self.assertNotIn(banned, workflow_source)

    def test_offline_payment_workflow_uses_tool_catalog_directly_and_s3_tid_comes_from_checklist(self):
        connection = create_connection()
        try:
            workflow = build_offline_payment_workflow(connection)
            self.assertTrue(hasattr(workflow, "tool_catalog"))
            self.assertFalse(hasattr(workflow, "planner"))

            result = workflow.run_scenario(
                "S3",
                operator_id="OP-DEMO",
                trace_id="TRACE-CHECKLIST-S3",
            )
        finally:
            connection.close()

        tool_names = [response.tool_name for response in result.tool_responses]
        self.assertIn("get_tid_config", tool_names)
        tid_trace = [
            item for item in result.policy_check_trace
            if item.get("tool_name") == "get_tid_config"
        ]
        self.assertTrue(tid_trace)
        self.assertEqual(tid_trace[0]["matched_data_need"], "payment_identifier_config")
        self.assertEqual(tid_trace[0]["policy_id"], "SOP-PAY-OP-003")
        self.assertEqual(tid_trace[0]["source"], "checklist_extractor")
        self.assertTrue(tid_trace[0]["source_quote"])


if __name__ == "__main__":
    unittest.main()