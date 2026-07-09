import unittest

from storeops.infra.database import create_database
from storeops.domains.offline_payment_ops.scenario_runtime import ScenarioGateway, seed_all_scenarios


class ToolMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_database()
        seed_all_scenarios(self.connection)
        self.gateway = ScenarioGateway(
            self.connection,
            scenario_id="S2",
            operator_id="OP-DEMO",
            trace_id="TRACE-METADATA",
        )

    def tearDown(self) -> None:
        self.connection.close()

    def test_tool_response_has_record_level_provenance(self) -> None:
        response = self.gateway.get_terminal_identity("STR-S2")

        self.assertTrue(response.provenance)
        self.assertTrue(
            all(":" in item for item in response.provenance),
            response.provenance,
        )
        self.assertEqual("current", response.freshness)

    def test_historical_tool_can_report_delayed_freshness(self) -> None:
        self.connection.execute(
            """
            UPDATE installation_events
            SET available_at = '2026-06-21T14:31:01+09:00'
            WHERE installation_event_id = 'INST-S2'
            """
        )
        self.connection.commit()

        response = self.gateway.get_installation_history("STR-S2")

        self.assertEqual("delayed", response.freshness)
        self.assertTrue(response.warnings)


if __name__ == "__main__":
    unittest.main()
