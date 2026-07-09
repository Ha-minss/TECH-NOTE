import sqlite3
import unittest

from storeops.core.types import ParsedCase
from storeops.core.workflow import Workflow
from storeops.core.planner import ToolCatalog, ToolSpec
from storeops.core.policy_checks import EvidencePlanBuilder, PolicyCheck
from storeops.core.contracts import (
    Assessment,
    CaseBrief,
    CauseAssessment,
    EvidenceRecord,
    ToolResponse,
    ToolStatus,
    WorkflowState,
)


class _FakeParser:
    def __init__(self):
        self.calls = []

    def parse(self, merchant_message: str, *, store_id: str, case_hint: str | None = None) -> ParsedCase:
        self.calls.append((merchant_message, store_id, case_hint))
        return ParsedCase(
            store_id=store_id,
            merchant_message=merchant_message,
            issue_family="generic_issue",
            symptoms=["slow"],
            context_flags=["opened_recently"],
            missing_fields=[],
            retrieval_query="generic retrieval query",
            planner_query="generic planner query",
        )


class _FakeRetriever:
    def __init__(self):
        self.queries = []

    def search(self, query: str, top_k: int = 3):
        self.queries.append((query, top_k))
        return [type("Policy", (), {"document_id": "POL-1", "title": "Policy 1", "content": "Check generic data."})()]


class _FakeChecklistExtractor:
    def __init__(self):
        self.calls = []
        self.last_trace = None

    def extract(self, *, parsed_case, query: str, retrieved_policies, tool_catalog) -> list[PolicyCheck]:
        self.calls.append((query, [item.document_id for item in retrieved_policies], parsed_case.issue_family, tool_catalog))
        return [
            PolicyCheck(
                policy_id="POL-1",
                policy_title="Policy 1",
                check_text="Check generic data.",
                matched_data_need="generic_need",
                priority="required",
                reason="SOP requires generic data before reasoning.",
                source_quote="Check generic data.",
            )
        ]


class _FakeExecutor:
    def __init__(self):
        self.calls = []

    def execute(self, *, store_id: str, plan) -> list[ToolResponse]:
        self.calls.append((store_id, [item.tool_name for item in plan.planned_tool_calls]))
        return [
            ToolResponse(
                tool_name="get_generic_data",
                trace_id="TRACE-1",
                store_id=store_id,
                status=ToolStatus.SUCCESS,
                data=[{"record_id": "ROW-1", "status": "ok"}],
                provenance=["synthetic"],
            )
        ]


class _FakeEvidenceBuilder:
    def __init__(self):
        self.calls = []

    def build(self, *, scenario_id: str, tool_responses):
        responses = list(tool_responses)
        self.calls.append((scenario_id, [item.tool_name for item in responses]))
        return [
            EvidenceRecord(
                evidence_id="EV-1",
                source_tool="get_generic_data",
                source_record_id="ROW-1",
                fact_type="generic_fact",
                normalized_value={"status": "ok"},
                observed_at="2026-06-20T17:00:00+09:00",
                supports=["generic_cause"],
            )
        ]


class _FakeReasoner:
    def __init__(self):
        self.calls = []

    def reason(self, *, evidence, parsed_case):
        self.calls.append(([item.evidence_id for item in evidence], parsed_case.issue_family))
        return CauseAssessment(
            primary_cause="generic_cause",
            assessment=Assessment.LIKELY,
            supporting_evidence_ids=["EV-1"],
            next_checks=["confirm_generic_fact"],
            forbidden_actions=["dangerous_write"],
        )


class _FakeSafetyGate:
    def __init__(self):
        self.calls = []

    def apply(self, *, parsed_case, planned_required_tools, tool_responses, evidence, cause_assessment):
        self.calls.append((parsed_case.issue_family, planned_required_tools, [item.tool_name for item in tool_responses]))
        from storeops.core.types import SafetyDecision
        return SafetyDecision(state=WorkflowState.READY_FOR_REVIEW, cause=cause_assessment)


class _FakeClarificationGenerator:
    def __init__(self):
        self.called = False

    def generate(self, *, parsed_case):
        self.called = True
        return []


class _FakeResponseDrafter:
    def __init__(self):
        self.calls = []

    def draft(self, **kwargs):
        self.calls.append(kwargs)
        return "Generic drafted response"


class CoreWorkflowTests(unittest.TestCase):
    def test_core_workflow_builds_plan_from_sop_checklist_without_planner_dependency(self):
        parser = _FakeParser()
        retriever = _FakeRetriever()
        checklist_extractor = _FakeChecklistExtractor()
        tool_catalog = ToolCatalog([
            ToolSpec(
                tool_name="get_generic_data",
                description="Read generic evidence.",
                provides_data_needs=["generic_need"],
                input_schema={"store_id": "string"},
                read_only=True,
                stage="pre_assessment",
            )
        ])
        executors = []

        def executor_factory(connection, *, operator_id: str, trace_id: str, scenario_id: str):
            self.assertIsInstance(connection, sqlite3.Connection)
            self.assertEqual(operator_id, "OP-1")
            self.assertEqual(trace_id, "TRACE-1")
            self.assertEqual(scenario_id, "GEN-1")
            executor = _FakeExecutor()
            executors.append(executor)
            return executor

        evidence_builder = _FakeEvidenceBuilder()
        reasoner = _FakeReasoner()
        safety_gate = _FakeSafetyGate()
        clarification_generator = _FakeClarificationGenerator()
        response_drafter = _FakeResponseDrafter()
        workflow = Workflow(
            connection=sqlite3.connect(":memory:"),
            parser=parser,
            retriever=retriever,
            tool_catalog=tool_catalog,
            checklist_extractor=checklist_extractor,
            evidence_plan_builder=EvidencePlanBuilder(),
            executor_factory=executor_factory,
            evidence_builder=evidence_builder,
            reasoner=reasoner,
            safety_gate=safety_gate,
            brief_builder=lambda decision, state: CaseBrief(
                cause=decision.cause,
                state=decision.state,
                operator_actions=["confirm_generic_fact"],
                recommended_route="generic_owner",
                merchant_response="Generic fallback response",
            ),
            confirmation_fact_formatter=lambda evidence: [f"{record.fact_type}:{record.normalized_value['status']}" for record in evidence],
            fallback_response_builder=lambda state, clarification_questions: "Generic fallback response",
            clarification_generator=clarification_generator,
            response_drafter=response_drafter,
        )

        try:
            result = workflow.run_case(
                scenario_id="GEN-1",
                store_id="STORE-1",
                merchant_message="please help",
                operator_id="OP-1",
                trace_id="TRACE-1",
                case_hint="generic",
            )
        finally:
            workflow.connection.close()

        self.assertFalse(hasattr(workflow, "planner"))
        self.assertEqual(parser.calls, [("please help", "STORE-1", "generic")])
        self.assertEqual(retriever.queries, [("generic retrieval query", 3)])
        self.assertEqual(checklist_extractor.calls, [("generic planner query", ["POL-1"], "generic_issue", tool_catalog)])
        self.assertEqual(len(executors), 1)
        self.assertEqual(executors[0].calls, [("STORE-1", ["get_generic_data"])])
        self.assertEqual(evidence_builder.calls, [("GEN-1", ["get_generic_data"])])
        self.assertEqual(reasoner.calls, [(["EV-1"], "generic_issue")])
        self.assertEqual(safety_gate.calls, [("generic_issue", ["get_generic_data"], ["get_generic_data"])])
        self.assertFalse(clarification_generator.called)
        self.assertEqual(result.policy_check_trace[0]["source"], "checklist_extractor")
        self.assertEqual(result.brief.recommended_route, "generic_owner")
        self.assertEqual(result.brief.merchant_response, "Generic drafted response")
        self.assertEqual(result.drafted_merchant_response, "Generic drafted response")
        self.assertEqual(result.retrieved_policy_ids, ["POL-1"])


if __name__ == "__main__":
    unittest.main()