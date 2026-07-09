import json
import os
import tempfile
import unittest
from pathlib import Path

from storeops.llm.client import ScriptedLLMClient


class LlmDemoTests(unittest.TestCase):
    def test_live_llm_settings_load_from_local_json_file(self):
        from storeops.llm.providers.live import LiveLLMSettings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "live.local.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "api_key": "test-key",
                        "model_name": "json-capable-model",
                        "base_url": "https://llm-gateway.example/v1",
                        "timeout_seconds": 25,
                    }
                ),
                encoding="utf-8",
            )

            settings = LiveLLMSettings.from_sources(config_path=settings_path)

            self.assertEqual(settings.api_key, "test-key")
            self.assertEqual(settings.model_name, "json-capable-model")
            self.assertEqual(settings.base_url, "https://llm-gateway.example/v1")
            self.assertEqual(settings.timeout_seconds, 25)

    def test_live_llm_settings_allow_env_override(self):
        from storeops.llm.providers.live import LiveLLMSettings

        old_values = {
            key: os.environ.get(key)
            for key in [
                "LIVE_LLM_API_KEY",
                "LIVE_LLM_MODEL",
                "LIVE_LLM_BASE_URL",
                "LIVE_LLM_TIMEOUT_SECONDS",
            ]
        }
        try:
            os.environ["LIVE_LLM_API_KEY"] = "env-key"
            os.environ["LIVE_LLM_MODEL"] = "env-json-model"
            os.environ["LIVE_LLM_BASE_URL"] = "https://env-gateway.example/v1"
            os.environ["LIVE_LLM_TIMEOUT_SECONDS"] = "12"

            settings = LiveLLMSettings.from_sources(config_path=None)

            self.assertEqual(settings.api_key, "env-key")
            self.assertEqual(settings.model_name, "env-json-model")
            self.assertEqual(settings.base_url, "https://env-gateway.example/v1")
            self.assertEqual(settings.timeout_seconds, 12)
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_demo_runner_outputs_clarification_questions_with_scripted_client(self):
        from storeops.apps.demo import run_demo_case

        payload = run_demo_case(
            "S5",
            client=ScriptedLLMClient(
                {
                    "case_parser": [
                        {
                            "issue_family": "payment_approval_failure",
                            "symptoms": ["approval_failure"],
                            "context_flags": ["new_terminal_recently_installed"],
                            "missing_fields": ["failed_physical_terminal", "visible_error_message"],
                            "confidence": 0.91,
                            "reasoning_summary": "clarification needed",
                        }
                    ],
                    "checklist_extractor": [
                        {
                            "policy_checks": [],
                            "confidence": 0.88,
                        }
                    ],
                    "clarification": [
                        {
                            "questions": [
                                {
                                    "field": "failed_physical_terminal",
                                    "question": "오류가 발생한 단말기가 어떤 기기인지 알려주세요.",
                                    "why_needed": "문제가 발생한 기기를 특정해야 합니다.",
                                },
                                {
                                    "field": "visible_error_message",
                                    "question": "화면에 표시된 오류 문구를 알려주세요.",
                                    "why_needed": "오류 유형을 구분해야 합니다.",
                                },
                            ],
                            "confidence": 0.92,
                        }
                    ],
                    "merchant_response": [
                        {
                            "merchant_response": "현재 확인된 기록만으로는 원인을 확정하기 어려워 추가 정보 확인이 필요합니다.",
                            "mentions_uncertainty": True,
                            "contains_unconfirmed_claim": False,
                            "confidence": 0.94,
                        }
                    ],
                }
            ),
            model_name="scripted-demo",
        )

        self.assertEqual(payload["state"], "NEEDS_CLARIFICATION")
        self.assertEqual(len(payload["clarification_questions"]), 2)
        self.assertIn("추가 정보 확인", payload["merchant_response"])
        self.assertEqual(payload["provider"], "custom-client")
        self.assertEqual(len(payload["llm_traces"]), 4)
        prompt_names = {trace["prompt_name"] for trace in payload["llm_traces"]}
        self.assertIn("checklist_extractor", prompt_names)
        self.assertNotIn("planner", prompt_names)

    def test_demo_runner_default_scripted_copy_is_readable(self):
        from storeops.apps.demo import run_demo_case

        payload = run_demo_case("S5")
        serialized = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(payload["provider"], "scripted-demo")
        self.assertEqual(payload["state"], "NEEDS_CLARIFICATION")
        self.assertEqual(len(payload["clarification_questions"]), 2)
        self.assertNotIn("???", serialized)
        self.assertIn("which terminal failed", payload["merchant_response"])
        self.assertIn("error message", payload["clarification_questions"][1])

    def test_demo_cli_accepts_scripted_demo_provider_alias(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from storeops.apps.demo import main

        output = StringIO()
        with redirect_stdout(output):
            main(["S5", "--provider", "scripted-demo", "--model", "scripted-demo"])

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["provider"], "scripted-demo")
        self.assertEqual(payload["state"], "NEEDS_CLARIFICATION")

    def test_live_llm_client_builds_contract_payload(self):
        from unittest.mock import patch

        from storeops.llm.models import LLMModelConfig
        from storeops.llm.providers.live import LiveLLMClient, LiveLLMSettings

        captured: dict[str, object] = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "case_type": "ambiguous_payment_failure",
                                            "selected_data_needs": [
                                                {
                                                    "name": "approval_failure_history",
                                                    "priority": "required",
                                                    "reason": "승인 실패 이력을 확인해야 합니다.",
                                                }
                                            ],
                                            "clarification_candidates": ["visible_error_message"],
                                            "forbidden_actions": ["config_mutation"],
                                            "confidence": 0.91,
                                        }
                                    )
                                },
                                "finish_reason": "stop",
                            }
                        ]
                    }
                ).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        settings = LiveLLMSettings(
            api_key="test-key",
            model_name="json-capable-model",
            base_url="https://llm-gateway.example/v1",
            timeout_seconds=12,
        )
        client = LiveLLMClient(settings)
        payload = {
            "query": "새 단말기 설치 후 승인 오류",
            "issue_family": "payment_approval_failure",
            "allowed_data_needs": ["approval_failure_history", "terminal_inventory"],
            "retrieved_policy_ids": ["SOP-PAY-OP-001"],
            "missing_fields": ["visible_error_message"],
        }
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = client.generate_json(
                prompt_name="planner",
                payload=payload,
                model=LLMModelConfig(model_name="fallback-model"),
            )

        self.assertEqual(result["case_type"], "ambiguous_payment_failure")
        self.assertEqual(captured["url"], "https://llm-gateway.example/v1/chat/completions")
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(captured["body"]["model"], "json-capable-model")
        user_content = captured["body"]["messages"][1]["content"]
        self.assertIn("allowed_data_needs", user_content)
        self.assertIn("Do not invent new tools", user_content)

    def test_llm_integration_doc_and_local_config_template_exist(self):
        repo_root = Path(__file__).resolve().parents[1]

        self.assertTrue((repo_root / "docs" / "llm-integration.md").exists())
        self.assertTrue((repo_root / "config" / "live.local.example.json").exists())

        doc = (repo_root / "docs" / "llm-integration.md").read_text(encoding="utf-8")
        self.assertIn("provider-agnostic", doc)
        self.assertIn("live.local.json", doc)
        self.assertIn("LIVE_LLM_*", doc)
        self.assertIn("py -X utf8 -m storeops.apps.demo S5", doc)


if __name__ == "__main__":
    unittest.main()
