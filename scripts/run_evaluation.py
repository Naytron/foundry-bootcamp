"""Run deterministic checks and optionally submit results to Foundry cloud evaluation."""

import argparse
import os
from pathlib import Path

from support_assistant.evaluation.cloud import run_cloud_evaluation
from support_assistant.evaluation.local import run_local_evaluation
from support_assistant.identity import create_credential


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SERVICE_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("BOOTCAMP_ACCESS_TOKEN"))
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/evaluations/support-agent.jsonl"),
    )
    parser.add_argument(
        "--knowledge-base",
        type=Path,
        default=Path("data/knowledge-base"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".foundry/results/local-evaluation.json"),
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Submit prepared responses to Microsoft Foundry cloud evaluation.",
    )
    return parser.parse_args()


def main() -> int:
    """Run local quality gates and return a process-friendly result."""
    args = _arguments()
    if not args.token:
        raise SystemExit("Set BOOTCAMP_ACCESS_TOKEN or pass --token")

    summary = run_local_evaluation(
        base_url=args.base_url,
        token=args.token,
        dataset_path=args.dataset,
        knowledge_base_path=args.knowledge_base,
        output_path=args.output,
    )
    print(
        f"Local evaluation: {summary.passed}/{summary.total} passed "
        f"({summary.pass_rate:.0%}). Results: {args.output}"
    )

    if args.cloud:
        from support_assistant.config import Settings

        settings = Settings()
        if not settings.foundry_project_endpoint or not settings.foundry_model:
            raise SystemExit("FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL are required")
        credential = create_credential(settings)
        try:
            cloud_output = args.output.with_name("cloud-evaluation.json")
            result = run_cloud_evaluation(
                project_endpoint=str(settings.foundry_project_endpoint).rstrip("/"),
                judge_model=settings.foundry_model,
                dataset_path=Path(summary.prepared_cloud_dataset),
                output_path=cloud_output,
                credential=credential,
            )
        finally:
            credential.close()
        print(f"Cloud evaluation completed: {result['report_url']}")

    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
