import unittest
from pathlib import Path


class ProjectContractTests(unittest.TestCase):
    def test_root_entries_match_final_submission_shape(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actual = {
            path.name
            for path in root.iterdir()
            if not path.name.startswith('.')
        }
        self.assertEqual(
            {
                'README.md',
                'pyproject.toml',
                'config',
                'data',
                'docs',
                'tests',
                'src',
                'reports',
                'scripts',
            },
            actual,
        )

    def test_storeops_top_level_entries_match_final_submission_shape(self) -> None:
        package_root = Path(__file__).resolve().parents[1] / 'src' / 'storeops'
        actual = {
            path.name
            for path in package_root.iterdir()
            if path.name != '__pycache__'
        }
        self.assertEqual(
            {
                '__init__.py',
                'apps',
                'core',
                'domains',
                'llm',
                'operator',
                'evals',
                'observability',
                'feedback_loop',
                'infra',
            },
            actual,
        )


if __name__ == '__main__':
    unittest.main()
