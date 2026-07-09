import unittest
from pathlib import Path

from storeops.core.evidence import EvidenceBuilder
from storeops.core.executor import ToolExecutor
from storeops.core.planner import Planner
from storeops.core.reasoner import EvidenceReasoner
from storeops.core.retrieval import HybridPolicyRetriever
from storeops.core.safety import SafetyGate
from storeops.infra.database import create_database, seed_s1
from storeops.domains.offline_payment_ops.evidence_rules import OfflinePaymentEvidenceBuilder
from storeops.domains.offline_payment_ops.fixtures import seed_offline_payment_scenarios
from storeops.domains.offline_payment_ops.parser import OfflinePaymentCaseParser
from storeops.domains.offline_payment_ops.reasoner_rules import OfflinePaymentReasoner
from storeops.domains.offline_payment_ops.tool_gateway import OfflinePaymentToolGateway
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow
from storeops.core.contracts import WorkflowState


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_core_and_domain_import_paths_are_explicit(self):
        self.assertTrue(issubclass(OfflinePaymentEvidenceBuilder, EvidenceBuilder))
        self.assertTrue(issubclass(OfflinePaymentReasoner, EvidenceReasoner))
        self.assertIsNotNone(OfflinePaymentCaseParser)
        self.assertIsNotNone(OfflinePaymentToolGateway)
        self.assertIsNotNone(ToolExecutor)
        self.assertIsNotNone(Planner)
        self.assertIsNotNone(HybridPolicyRetriever)
        self.assertIsNotNone(SafetyGate)

    def test_offline_payment_workflow_uses_domain_pack_by_default(self):
        connection = create_database()
        try:
            seed_s1(connection)
            seed_offline_payment_scenarios(connection)
            result = OfflinePaymentWorkflow.default(connection).run_scenario(
                "S1",
                operator_id="OP-DEMO",
                trace_id="TRACE-ARCH",
            )
        finally:
            connection.close()

        self.assertEqual(result.state.current_state, WorkflowState.READY_FOR_REVIEW)
        self.assertEqual(result.brief.cause.primary_cause, "duplicate_tid")

    def test_core_interfaces_expose_generic_protocols(self):
        import importlib

        module = importlib.import_module("storeops.core.interfaces")

        self.assertTrue(hasattr(module, "CaseParser"))
        self.assertTrue(hasattr(module, "ToolExecutorProtocol"))
        self.assertTrue(hasattr(module, "EvidenceBuilder"))
        self.assertTrue(hasattr(module, "EvidenceReasoner"))
        self.assertTrue(hasattr(module, "SafetyGateProtocol"))

    def test_core_files_do_not_embed_offline_payment_cause_terms(self):
        files = [
            Path("src/storeops/core/interfaces.py"),
            Path("src/storeops/core/evidence.py"),
            Path("src/storeops/core/reasoner.py"),
            Path("src/storeops/core/safety.py"),
            Path("src/storeops/core/workflow.py"),
        ]

        for path in files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for forbidden in [
                    "duplicate_tid",
                    "terminal_identifier_mismatch",
                    "van_merchant_registration_missing",
                    "pos_front_connection_issue",
                ]:
                    self.assertNotIn(forbidden, text)

    def test_domain_workflow_builder_owns_offline_payment_wiring(self):
        text = Path("src/storeops/domains/offline_payment_ops/workflow.py").read_text(encoding="utf-8")

        self.assertIn("def build_offline_payment_workflow", text)
        self.assertIn("class OfflinePaymentWorkflow", text)
        self.assertIn("OfflinePaymentCaseParser", text)
        self.assertIn("OfflinePaymentEvidenceBuilder", text)
        self.assertIn("OfflinePaymentReasoner", text)
        self.assertIn("HybridPolicyRetriever.from_policy_dir", text)

    def test_removed_wrapper_paths_are_absent(self):
        disallowed = [
            Path("src/storeops") / "sta" "ge2",
            Path("src/storeops") / "sta" "ge3_cli.py",
            Path("src/storeops") / "sta" "ge3_web.py",
            Path("src/storeops") / "sta" "ge5_release.py",
            Path("src/storeops") / "sta" "ge6_demo.py",
            Path("README_" + "STAGE1.md"),
        ]

        for path in disallowed:
            with self.subTest(path=path):
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
