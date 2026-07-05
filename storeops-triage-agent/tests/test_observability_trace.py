import json
import unittest

from storeops.observability.serialization import trace_to_json
from storeops.observability.trace import build_trace_record
from storeops.apps.operator_cli import create_connection
from storeops.domains.offline_payment_ops.workflow import OfflinePaymentWorkflow


class ObservabilityTraceTests(unittest.TestCase):
    def test_trace_record_is_emitted_for_workflow_run(self):
        connection = create_connection()
        try:
            workflow = OfflinePaymentWorkflow.default(connection)
            result = workflow.run_scenario("S1", operator_id="OP-DEMO", trace_id="TRACE-OBS-S1")
        finally:
            connection.close()

        record = build_trace_record(result)

        self.assertEqual(record.trace_id, "TRACE-OBS-S1")
        self.assertEqual(record.final_state, "READY_FOR_REVIEW")
        self.assertEqual(record.final_cause, "duplicate_tid")
        self.assertTrue(record.evidence_ids)

    def test_trace_record_is_json_serializable(self):
        connection = create_connection()
        try:
            workflow = OfflinePaymentWorkflow.default(connection)
            result = workflow.run_scenario("S7", operator_id="OP-DEMO", trace_id="TRACE-OBS-S7")
        finally:
            connection.close()

        payload = trace_to_json(build_trace_record(result))

        self.assertIn('"trace_id": "TRACE-OBS-S7"', payload)
        json.loads(payload)


if __name__ == "__main__":
    unittest.main()
