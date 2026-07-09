import json
import tempfile
import unittest
from pathlib import Path

from storeops.infra.fixture_persistence import export_synthetic_fixtures


class FixturePersistenceTests(unittest.TestCase):
    def test_export_writes_sqlite_and_json_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = export_synthetic_fixtures(Path(temp_dir))

            self.assertTrue(output.sqlite_path.exists())
            self.assertTrue(output.manifest_path.exists())
            self.assertEqual("offline_payment_ops.sqlite3", output.sqlite_path.name)
            self.assertEqual("offline_payment_ops_manifest.json", output.manifest_path.name)
            manifest = json.loads(output.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("offline-payment-ops-v1", manifest["fixture_version"])
            self.assertEqual(
                ["S1", "S2", "S3", "S4", "S5", "S6A", "S6B", "S7"],
                manifest["scenario_ids"],
            )
            self.assertNotIn("root_cause", output.manifest_path.read_text())


if __name__ == "__main__":
    unittest.main()

