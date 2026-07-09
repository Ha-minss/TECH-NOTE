import unittest

from storeops.core.safety import SafetyGate
from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.evidence_rules import OfflinePaymentEvidenceBuilder
from storeops.domains.offline_payment_ops.parser import OfflinePaymentCaseParser
from storeops.domains.offline_payment_ops.reasoner_rules import OfflinePaymentReasoner
from storeops.domains.offline_payment_ops.safety_rules import OFFLINE_PAYMENT_FORBIDDEN_ACTIONS
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentToolExecutor, OfflinePaymentWorkflow
from storeops.domains.offline_payment_ops.scenario_runtime import seed_all_scenarios
from storeops.core.contracts import Assessment, ToolStatus, WorkflowState


class OfflinePaymentWorkflowTests(unittest.TestCase):

    def _plan_from_policy_checklist(self, workflow, parsed):
        retrieved = workflow.retriever.search(parsed.retrieval_query, top_k=3)
        policy_checks = workflow.checklist_extractor.extract(
            parsed_case=parsed,
            query=parsed.planner_query,
            retrieved_policies=retrieved,
            tool_catalog=workflow.tool_catalog,
        )
        plan, _trace = workflow.evidence_plan_builder.build(
            policy_checks=policy_checks,
            tool_catalog=workflow.tool_catalog,
            retrieved_policy_ids=[result.document_id for result in retrieved],
        )
        return plan

    def setUp(self):
        self.connection = create_database()
        seed_s1(self.connection)
        seed_all_scenarios(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_case_parser_extracts_installation_context_and_missing_fields(self):
        parsed = OfflinePaymentCaseParser().parse(
            "new terminal installed and existing terminal card approval failed",
            store_id="STR-S1",
        )

        self.assertEqual(parsed.issue_family, "payment_approval_failure")
        self.assertIn("new_terminal_recently_installed", parsed.context_flags)
        self.assertIn("failed_physical_terminal", parsed.missing_fields)
        self.assertIn("visible_error_message", parsed.missing_fields)

    def test_tool_executor_runs_planned_read_only_calls(self):
        workflow = OfflinePaymentWorkflow.default(self.connection)
        parsed = workflow.parser.parse(
            "new terminal installed and existing terminal payment failed",
            store_id="STR-S1",
        )
        plan = self._plan_from_policy_checklist(workflow, parsed)

        responses = OfflinePaymentToolExecutor(
            self.connection,
            operator_id="OP-DEMO",
            trace_id="TRACE-RUNTIME",
            scenario_id="S1",
        ).execute(store_id="STR-S1", plan=plan)

        self.assertIn("get_tid_config", {response.tool_name for response in responses})
        self.assertTrue(all(response.status in set(ToolStatus) for response in responses))

    def test_evidence_builder_normalizes_duplicate_tid_evidence(self):
        workflow = OfflinePaymentWorkflow.default(self.connection)
        result = workflow.run_scenario("S1", operator_id="OP-DEMO", trace_id="TRACE-S1-EVIDENCE")
        evidence = result.evidence

        self.assertTrue(any(record.fact_type == "duplicate_tid_assignment" for record in evidence))
        self.assertTrue(any("duplicate_tid" in record.supports for record in evidence))

    def test_reasoner_prioritizes_duplicate_tid_from_domain_rules(self):
        workflow = OfflinePaymentWorkflow.default(self.connection)
        result = workflow.run_scenario("S1", operator_id="OP-DEMO", trace_id="TRACE-S1-REASON")
        cause = result.brief.cause

        self.assertEqual(cause.primary_cause, "duplicate_tid")
        self.assertEqual(cause.next_checks, ["confirm_tid_mapping_with_installation_owner"])
        self.assertEqual(cause.forbidden_actions, OFFLINE_PAYMENT_FORBIDDEN_ACTIONS)
        self.assertTrue(cause.supporting_evidence_ids)

    def test_safety_gate_moves_to_conflict_review_when_evidence_conflicts(self):
        assessment = SafetyGate().apply(
            parsed_case=OfflinePaymentCaseParser().parse("payment approval failure", store_id="STR-S7"),
            planned_required_tools=[],
            tool_responses=[],
            evidence=[],
            cause_assessment={
                "primary_cause": None,
                "assessment": Assessment.NEEDS_CONFIRMATION,
                "supporting_evidence_ids": ["EV-S7-1"],
                "contradicting_evidence_ids": ["EV-S7-2"],
                "alternative_causes": ["temporary_duplicate_tid"],
                "missing_evidence": [],
                "next_checks": ["inspect_incident_time_tid_history"],
                "forbidden_actions": OFFLINE_PAYMENT_FORBIDDEN_ACTIONS,
            },
        )

        self.assertEqual(assessment.state, WorkflowState.CONFLICT_REVIEW)

    def test_safety_gate_requests_clarification_when_cause_missing_and_fields_missing(self):
        parsed_case = OfflinePaymentCaseParser().parse("card approval failure", store_id="STR-S5")

        assessment = SafetyGate().apply(
            parsed_case=parsed_case,
            planned_required_tools=[],
            tool_responses=[],
            evidence=[],
            cause_assessment={
                "primary_cause": None,
                "assessment": Assessment.UNAVAILABLE,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "alternative_causes": [],
                "missing_evidence": [],
                "next_checks": ["request_missing_merchant_context"],
                "forbidden_actions": OFFLINE_PAYMENT_FORBIDDEN_ACTIONS,
            },
        )

        self.assertEqual(assessment.state, WorkflowState.NEEDS_CLARIFICATION)

    def test_safety_gate_blocks_likely_claim_without_supporting_evidence(self):
        assessment = SafetyGate().apply(
            parsed_case=OfflinePaymentCaseParser().parse("card approval failure", store_id="STR-S5"),
            planned_required_tools=["get_recent_approval_errors"],
            tool_responses=[],
            evidence=[],
            cause_assessment={
                "primary_cause": "duplicate_tid",
                "assessment": Assessment.LIKELY,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "alternative_causes": [],
                "missing_evidence": [],
                "next_checks": [],
                "forbidden_actions": [],
            },
        )

        self.assertEqual(assessment.state, WorkflowState.DEGRADED_REVIEW)
        self.assertNotEqual(assessment.cause.assessment, Assessment.LIKELY)

    def test_s1_to_s7_workflow_reaches_expected_state_and_cause_or_abstention(self):
        workflow = OfflinePaymentWorkflow.default(self.connection)
        expected = {
            "S1": (WorkflowState.READY_FOR_REVIEW, "duplicate_tid"),
            "S2": (WorkflowState.READY_FOR_REVIEW, "terminal_identifier_mismatch"),
            "S3": (WorkflowState.READY_FOR_REVIEW, "van_merchant_registration_missing"),
            "S4": (WorkflowState.READY_FOR_REVIEW, "pos_front_connection_issue"),
            "S5": (WorkflowState.NEEDS_CLARIFICATION, None),
            "S6A": (WorkflowState.DEGRADED_REVIEW, None),
            "S6B": (WorkflowState.READY_FOR_REVIEW, "duplicate_tid"),
            "S7": (WorkflowState.CONFLICT_REVIEW, None),
        }

        failures = []
        for scenario_id, (expected_state, expected_cause) in expected.items():
            result = workflow.run_scenario(scenario_id, operator_id="OP-DEMO", trace_id=f"TRACE-{scenario_id}")
            actual = (result.state.current_state, result.brief.cause.primary_cause)
            if actual != (expected_state, expected_cause):
                failures.append({
                    "scenario_id": scenario_id,
                    "expected": (expected_state, expected_cause),
                    "actual": actual,
                    "tools": [response.tool_name for response in result.tool_responses],
                    "evidence": [record.fact_type for record in result.evidence],
                })
            if expected_cause is not None:
                self.assertTrue(result.brief.cause.supporting_evidence_ids, f"{scenario_id} must cite evidence for displayed cause")

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
