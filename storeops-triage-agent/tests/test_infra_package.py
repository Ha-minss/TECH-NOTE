import unittest

from storeops.infra.database import create_database as direct_create_database, seed_s1 as direct_seed_s1
from storeops.infra.fixture_persistence import export_synthetic_fixtures as direct_export_synthetic_fixtures
from storeops.infra.database import create_database as infra_create_database, seed_s1 as infra_seed_s1
from storeops.infra.fixture_persistence import export_synthetic_fixtures as infra_export_synthetic_fixtures
from storeops.infra.scenarios import ScenarioGateway as InfraScenarioGateway, seed_all_scenarios as infra_seed_all_scenarios
from storeops.infra.schemas import WorkflowState as InfraWorkflowState
from storeops.infra.tools import ToolGateway as InfraToolGateway
from storeops.infra.transitions import transition as infra_transition
from storeops.domains.offline_payment_ops.scenario_runtime import ScenarioGateway as DirectScenarioGateway, seed_all_scenarios as direct_seed_all_scenarios
from storeops.core.contracts import WorkflowState as DirectWorkflowState
from storeops.infra.tools import ToolGateway as DirectToolGateway
from storeops.operator.transitions import transition as direct_transition


class InfraPackageTests(unittest.TestCase):
    def test_infra_database_exports_existing_database_contract(self):
        self.assertIs(infra_create_database, direct_create_database)
        self.assertIs(infra_seed_s1, direct_seed_s1)

    def test_infra_schemas_exports_existing_schema_contract(self):
        self.assertIs(InfraWorkflowState, DirectWorkflowState)

    def test_infra_tools_exports_existing_tool_gateway_contract(self):
        self.assertIs(InfraToolGateway, DirectToolGateway)

    def test_infra_scenarios_exports_existing_scenario_contract(self):
        self.assertIs(InfraScenarioGateway, DirectScenarioGateway)
        self.assertIs(infra_seed_all_scenarios, direct_seed_all_scenarios)

    def test_infra_transitions_exports_existing_transition_contract(self):
        self.assertIs(infra_transition, direct_transition)

    def test_infra_fixture_persistence_exports_existing_persistence_contract(self):
        self.assertIs(infra_export_synthetic_fixtures, direct_export_synthetic_fixtures)


if __name__ == "__main__":
    unittest.main()
