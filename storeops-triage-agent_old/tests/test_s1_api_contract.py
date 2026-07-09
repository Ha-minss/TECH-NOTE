import unittest

from storeops import database, tools
from storeops.apps import operator_cli


class S1ApiContractTests(unittest.TestCase):
    def test_operator_cli_runtime_api_exists(self) -> None:
        expected = {
            database: ["create_database", "seed_s1"],
            tools: ["ToolGateway"],
            operator_cli: ["create_connection", "run", "run_view_model"],
        }

        missing = []
        for module, names in expected.items():
            missing.extend(
                f"{module.__name__}.{name}"
                for name in names
                if not hasattr(module, name)
            )

        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
