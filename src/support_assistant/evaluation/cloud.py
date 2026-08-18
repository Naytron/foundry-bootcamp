"""Optional Microsoft Foundry cloud evaluation over prepared responses."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
from azure.core.credentials import TokenCredential
from azure.core.exceptions import AzureError
from openai import OpenAIError
from openai.types.eval_create_params import DataSourceConfigCustom
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileID,
)


class CloudEvaluationError(RuntimeError):
    """Raised when a Foundry cloud evaluation fails or times out."""


def run_cloud_evaluation(
    *,
    project_endpoint: str,
    judge_model: str,
    dataset_path: Path,
    output_path: Path,
    credential: TokenCredential,
    timeout_seconds: int = 600,
    poll_seconds: int = 5,
) -> dict[str, Any]:
    """Upload prepared responses and run current Foundry built-in evaluators."""
    version = hashlib.sha256(dataset_path.read_bytes()).hexdigest()[:12]
    data_source_config = DataSourceConfigCustom(
        type="custom",
        item_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "response": {"type": "string"},
                "context": {"type": "string"},
                "ground_truth": {"type": "string"},
            },
            "required": ["query", "response", "context", "ground_truth"],
        },
        include_sample_schema=False,
    )
    criteria = _criteria(judge_model)

    try:
        with (
            AIProjectClient(endpoint=project_endpoint, credential=credential) as project,
            project.get_openai_client() as openai,
        ):
            uploaded_dataset = project.datasets.upload_file(
                name="foundry-bootcamp-support-evaluation",
                version=version,
                file_path=str(dataset_path),
            )
            if not uploaded_dataset.id:
                raise CloudEvaluationError("Foundry did not return a dataset ID")
            data_id = uploaded_dataset.id
            evaluation = openai.evals.create(
                name=f"support-evaluation-{version}",
                data_source_config=data_source_config,
                testing_criteria=criteria,
            )
            created_run = openai.evals.runs.create(
                eval_id=evaluation.id,
                name=f"support-run-{version}",
                data_source=CreateEvalJSONLRunDataSourceParam(
                    type="jsonl",
                    source=SourceFileID(type="file_id", id=data_id),
                ),
            )
            deadline = time.monotonic() + timeout_seconds
            run_id = created_run.id
            run_status = created_run.status
            report_url = created_run.report_url
            while run_status not in {"completed", "failed", "canceled"}:
                if time.monotonic() >= deadline:
                    raise CloudEvaluationError("Cloud evaluation timed out")
                time.sleep(poll_seconds)
                retrieved_run = openai.evals.runs.retrieve(
                    run_id=run_id,
                    eval_id=evaluation.id,
                )
                run_status = retrieved_run.status
                report_url = retrieved_run.report_url

            if run_status != "completed":
                raise CloudEvaluationError(f"Cloud evaluation ended with status {run_status}")

            items = list(
                openai.evals.runs.output_items.list(
                    run_id=run_id,
                    eval_id=evaluation.id,
                )
            )
            result = {
                "evaluation_id": evaluation.id,
                "run_id": run_id,
                "status": run_status,
                "report_url": report_url,
                "items": [_json_value(item) for item in items],
            }
    except (AzureError, OpenAIError, TimeoutError) as exc:
        raise CloudEvaluationError("Microsoft Foundry cloud evaluation failed") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _criteria(judge_model: str) -> list[TestingCriterionAzureAIEvaluator]:
    def criterion(
        name: str,
        evaluator_name: str,
        mapping: dict[str, str],
        *,
        initialization_parameter: str = "model",
    ) -> TestingCriterionAzureAIEvaluator:
        return TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name=name,
            evaluator_name=evaluator_name,
            initialization_parameters={initialization_parameter: judge_model},
            data_mapping=mapping,
        )

    query_response = {
        "query": "{{item.query}}",
        "response": "{{item.response}}",
    }
    return [
        criterion("relevance", "builtin.relevance", query_response),
        criterion(
            "groundedness",
            "builtin.groundedness",
            {**query_response, "context": "{{item.context}}"},
        ),
        criterion(
            "task_adherence",
            "builtin.task_adherence",
            query_response,
            initialization_parameter="deployment_name",
        ),
        criterion("intent_resolution", "builtin.intent_resolution", query_response),
        criterion("violence", "builtin.violence", query_response),
        criterion(
            "indirect_attack",
            "builtin.indirect_attack",
            {**query_response, "context": "{{item.context}}"},
        ),
    ]


def _json_value(value: object) -> object:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return str(value)
