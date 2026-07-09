import unittest

from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.operator.view_model import OperatorCaseViewModel
from storeops.domains.offline_payment_ops.parser import OfflinePaymentCaseParser
from storeops.domains.offline_payment_ops.parser import OfflinePaymentCaseParser as CaseParser
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow


class LLMLayerTests(unittest.TestCase):
    def setUp(self):
        from storeops.llm.case_parser import LLMCaseParser
        from storeops.llm.clarification import ClarificationQuestionGenerator
        from storeops.llm.client import ScriptedLLMClient
        from storeops.llm.drafting import MerchantResponseDrafter
        from storeops.llm.planner import LLMPlanner
        from storeops.core.planner import Planner
        from storeops.llm.runtime import LLMRuntime

        self.connection = create_database()
        seed_s1(self.connection)
        seed_offline_payment_scenarios(self.connection)
        self.base_workflow = OfflinePaymentWorkflow.default(self.connection)
        self.ScriptedLLMClient = ScriptedLLMClient
        self.LLMRuntime = LLMRuntime
        self.LLMCaseParser = LLMCaseParser
        self.ClarificationQuestionGenerator = ClarificationQuestionGenerator
        self.LLMPlanner = LLMPlanner
        self.Planner = Planner
        self.MerchantResponseDrafter = MerchantResponseDrafter

    def tearDown(self):
        self.connection.close()

    def test_llm_case_parser_falls_back_when_confidence_is_too_low(self):
        runtime = self.LLMRuntime(
            client=self.ScriptedLLMClient(
                {
                    "case_parser": [
                        {
                            "issue_family": "payment_approval_failure",
                            "symptoms": ["approval_failure"],
                            "context_flags": [],
                            "missing_fields": [],
                            "confidence": 0.21,
                            "reasoning_summary": "too uncertain",
                        }
                    ]
                }
            ),
            model_name="scripted-parser",
        )
        parser = self.LLMCaseParser(runtime=runtime, fallback_parser=CaseParser())

        parsed = parser.parse(
            "어제 새 단말기 설치했는데 기존 단말기 카드 승인이 안 돼요.",
            store_id="STR-S1",
        )

        self.assertIn("new_terminal_recently_installed", parsed.context_flags)
        self.assertTrue(parser.last_trace.used_fallback)

    def test_llm_planner_maps_allowed_data_needs_to_real_tool_calls(self):
        runtime = self.LLMRuntime(
            client=self.ScriptedLLMClient(
                {
                    "planner": [
                        {
                            "case_type": "terminal_installation_payment_failure",
                            "selected_data_needs": [
                                {
                                    "name": "payment_identifier_config",
                                    "priority": "required",
                                    "reason": "TID 설정을 확인해야 합니다.",
                                },
                                {
                                    "name": "activation_timeline",
                                    "priority": "required",
                                    "reason": "개시 시점을 비교해야 합니다.",
                                },
                            ],
                            "clarification_candidates": [],
                            "forbidden_actions": ["config_mutation"],
                            "confidence": 0.94,
                        }
                    ]
                }
            ),
            model_name="scripted-planner",
        )
        fallback_planner = self.Planner(tool_catalog=self.base_workflow.tool_catalog)
        planner = self.LLMPlanner(
            runtime=runtime,
            tool_catalog=self.base_workflow.tool_catalog,
            fallback_planner=fallback_planner,
        )
        parsed = OfflinePaymentCaseParser().parse(
            "새 단말기 설치 후 기존 단말기 결제가 안 됩니다.",
            store_id="STR-S1",
            case_hint="duplicate TID new terminal installation payment approval failure",
        )
        retrieved = self.base_workflow.retriever.search(parsed.retrieval_query, top_k=3)

        plan = planner.plan(
            query=parsed.planner_query,
            retrieved_policies=retrieved,
            parsed_case=parsed,
        )

        self.assertEqual(plan.case_type, "terminal_installation_payment_failure")
        self.assertIn("get_tid_config", {call.tool_name for call in plan.planned_tool_calls})
        self.assertIn("get_activation_history", {call.tool_name for call in plan.planned_tool_calls})
        self.assertFalse(planner.last_trace.used_fallback)

    def test_clarification_generator_limits_questions_to_merchant_observable_fields(self):
        runtime = self.LLMRuntime(
            client=self.ScriptedLLMClient(
                {
                    "clarification": [
                        {
                            "questions": [
                                {
                                    "field": "failed_physical_terminal",
                                    "question": "어느 단말기에서 오류가 났는지 알려주세요.",
                                    "why_needed": "실패 단말기를 특정해야 합니다.",
                                },
                                {
                                    "field": "visible_error_message",
                                    "question": "단말기에 표시된 오류 문구를 알려주세요.",
                                    "why_needed": "오류 유형을 구분해야 합니다.",
                                },
                                {
                                    "field": "internal_tid_config",
                                    "question": "TID 값을 알려주세요.",
                                    "why_needed": "내부 설정을 봐야 합니다.",
                                },
                            ],
                            "confidence": 0.91,
                        }
                    ]
                }
            ),
            model_name="scripted-clarifier",
        )
        generator = self.ClarificationQuestionGenerator(runtime=runtime)
        parsed = OfflinePaymentCaseParser().parse(
            "카드 승인이 안 돼요.",
            store_id="STR-S5",
        )

        questions = generator.generate(parsed_case=parsed)

        self.assertEqual(len(questions), 2)
        self.assertEqual(
            [question.field for question in questions],
            ["failed_physical_terminal", "visible_error_message"],
        )

    def test_merchant_response_drafter_falls_back_on_unconfirmed_claim(self):
        runtime = self.LLMRuntime(
            client=self.ScriptedLLMClient(
                {
                    "merchant_response": [
                        {
                            "merchant_response": "이미 해결 완료되었으니 다시 결제하시면 됩니다.",
                            "mentions_uncertainty": False,
                            "contains_unconfirmed_claim": True,
                            "confidence": 0.96,
                        }
                    ]
                }
            ),
            model_name="scripted-drafter",
        )
        drafter = self.MerchantResponseDrafter(runtime=runtime)

        response = drafter.draft(
            state="NEEDS_CLARIFICATION",
            primary_cause=None,
            confirmed_facts=[],
            clarification_questions=["오류가 난 단말기를 알려주세요."],
            fallback_text="현재 확인된 기록만으로는 정확한 원인을 확정하기 어렵습니다.",
        )

        self.assertIn("정확한 원인을 확정하기 어렵습니다", response)
        self.assertTrue(drafter.last_trace.used_fallback)

    def test_llm_enabled_workflow_surfaces_questions_and_drafted_response(self):
        workflow = OfflinePaymentWorkflow.with_llm(
            self.connection,
            client=self.ScriptedLLMClient(
                {
                    "case_parser": [
                        {
                            "issue_family": "payment_approval_failure",
                            "symptoms": ["approval_failure"],
                            "context_flags": ["new_terminal_recently_installed"],
                            "missing_fields": ["failed_physical_terminal", "visible_error_message"],
                            "confidence": 0.93,
                            "reasoning_summary": "신규 설치 이후 승인 오류 맥락입니다.",
                        }
                    ],
                    "checklist_extractor": [
                        {
                            "policy_checks": [],
                            "confidence": 0.92,
                        }
                    ],
                    "clarification": [
                        {
                            "questions": [
                                {
                                    "field": "failed_physical_terminal",
                                    "question": "오류가 난 단말기가 기존 단말기인지 새 단말기인지 알려주세요.",
                                    "why_needed": "문제가 발생한 기기를 특정해야 합니다.",
                                },
                                {
                                    "field": "visible_error_message",
                                    "question": "단말기 화면에 표시된 오류 문구를 알려주세요.",
                                    "why_needed": "승인 실패 유형을 구분해야 합니다.",
                                },
                            ],
                            "confidence": 0.95,
                        }
                    ],
                    "merchant_response": [
                        {
                            "merchant_response": "현재 확인된 기록만으로는 원인을 확정할 수 없어, 오류가 난 단말기와 화면 문구를 먼저 확인 부탁드립니다.",
                            "mentions_uncertainty": True,
                            "contains_unconfirmed_claim": False,
                            "confidence": 0.97,
                        }
                    ],
                }
            ),
            model_name="scripted-workflow",
        )

        result = workflow.run_scenario(
            "S5",
            operator_id="OP-DEMO",
            trace_id="TRACE-LLM-S5",
        )
        view_model = OperatorCaseViewModel.from_workflow_result(result)

        self.assertEqual(result.state.current_state.value, "NEEDS_CLARIFICATION")
        self.assertEqual(len(result.clarification_questions), 2)
        self.assertIn("오류가 난 단말기", result.clarification_questions[0])
        self.assertIn("원인을 확정할 수 없어", result.drafted_merchant_response)
        self.assertEqual(view_model.merchant_response_draft, result.drafted_merchant_response)


if __name__ == "__main__":
    unittest.main()
