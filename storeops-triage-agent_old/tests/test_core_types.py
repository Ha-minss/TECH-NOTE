import unittest


class CoreTypesTests(unittest.TestCase):
    def test_core_types_module_exports_workflow_types(self):
        from storeops.core.types import ParsedCase, SafetyDecision, WorkflowResult

        self.assertEqual(ParsedCase.__name__, "ParsedCase")
        self.assertEqual(SafetyDecision.__name__, "SafetyDecision")
        self.assertEqual(WorkflowResult.__name__, "WorkflowResult")

    def test_domain_runtime_uses_core_workflow_types(self):
        from storeops.core.types import ParsedCase, SafetyDecision, WorkflowResult
        from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow

        self.assertIsNotNone(OfflinePaymentWorkflow)
        self.assertEqual(ParsedCase.__name__, "ParsedCase")
        self.assertEqual(SafetyDecision.__name__, "SafetyDecision")
        self.assertEqual(WorkflowResult.__name__, "WorkflowResult")


if __name__ == "__main__":
    unittest.main()
