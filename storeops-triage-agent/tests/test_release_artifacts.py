import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from storeops.apps.release_artifacts import DEMO_SCENARIOS, generate_release_artifacts


class ReleaseArtifactsTests(unittest.TestCase):
    def test_generate_release_artifacts_exports_demo_pages_and_eval_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            demo_dir = base_dir / 'docs' / 'demo'
            eval_dir = base_dir / 'data' / 'eval_reports' / 'latest'

            report = generate_release_artifacts(demo_dir=demo_dir, eval_output_dir=eval_dir)

            self.assertEqual(DEMO_SCENARIOS, tuple(report.demo_pages.keys()))
            for scenario_id, output_path in report.demo_pages.items():
                self.assertTrue(output_path.exists(), msg=scenario_id)
                self.assertEqual(output_path.name, f'{scenario_id}.html')
                self.assertEqual(output_path.parent, demo_dir)

            self.assertTrue((eval_dir / 'summary.json').exists())
            self.assertTrue((eval_dir / 'cases.json').exists())
            self.assertTrue((eval_dir / 'report.md').exists())

    def test_readme_points_to_docs_demo_output(self):
        repo_root = Path(__file__).resolve().parents[1]
        readme = (repo_root / 'README.md').read_text(encoding='utf-8')

        self.assertIn('docs/demo/', readme)
        self.assertNotIn('demo/static/', readme)


if __name__ == '__main__':
    unittest.main()
