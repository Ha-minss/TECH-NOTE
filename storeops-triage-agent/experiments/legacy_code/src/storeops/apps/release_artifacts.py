"""Release artifact generation for the hiring-facing portfolio."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from storeops.apps.operator_web import export_html
from storeops.evals.runner import EvaluationRunReport, run_full_evaluation

DEMO_SCENARIOS = ('S1', 'S5', 'S6A', 'S7')


@dataclass(frozen=True)
class ReleaseArtifacts:
    demo_pages: dict[str, Path]
    evaluation: EvaluationRunReport


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_demo_dir() -> Path:
    return project_root() / 'docs' / 'demo'


def export_demo_pages(
    demo_dir: Path | str | None = None,
    scenarios: tuple[str, ...] = DEMO_SCENARIOS,
) -> dict[str, Path]:
    target_dir = Path(demo_dir) if demo_dir is not None else default_demo_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    exported: dict[str, Path] = {}
    for scenario_id in scenarios:
        output_path = target_dir / f'{scenario_id}.html'
        export_html(scenario_id, output_path)
        exported[scenario_id] = output_path
    return exported


def generate_release_artifacts(
    demo_dir: Path | str | None = None,
    eval_output_dir: Path | str | None = None,
) -> ReleaseArtifacts:
    demo_pages = export_demo_pages(demo_dir=demo_dir)
    evaluation = run_full_evaluation(output_dir=eval_output_dir)
    return ReleaseArtifacts(demo_pages=demo_pages, evaluation=evaluation)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo-dir', default=None)
    parser.add_argument('--eval-dir', default=None)
    args = parser.parse_args()

    artifacts = generate_release_artifacts(demo_dir=args.demo_dir, eval_output_dir=args.eval_dir)
    payload = {
        'demo_pages': {scenario_id: str(path) for scenario_id, path in artifacts.demo_pages.items()},
        'evaluation_output_dir': str(artifacts.evaluation.output_dir),
        'evaluation_summary': artifacts.evaluation.summary,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = [
    'DEMO_SCENARIOS',
    'ReleaseArtifacts',
    'default_demo_dir',
    'export_demo_pages',
    'generate_release_artifacts',
    'project_root',
]


if __name__ == '__main__':
    main()
