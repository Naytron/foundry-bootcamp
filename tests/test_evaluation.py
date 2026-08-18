"""Local and cloud evaluation workflow tests."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from azure.core.exceptions import HttpResponseError

from support_assistant.evaluation.cloud import (
    CloudEvaluationError,
    _criteria,
    _json_value,
    run_cloud_evaluation,
)
from support_assistant.evaluation.local import (
    EvaluationInvocationError,
    evaluate_case,
    invoke_chat,
    load_evaluation_cases,
    run_local_evaluation,
)
from support_assistant.evaluation.models import Citation, EvaluationCase, InvocationResult

DATASET = Path("data/evaluations/support-agent.jsonl")
KNOWLEDGE = Path("data/knowledge-base")


def test_load_evaluation_cases_requires_rows_and_unique_ids(tmp_path: Path) -> None:
    assert len(load_evaluation_cases(DATASET)) == 8

    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="No evaluation cases"):
        load_evaluation_cases(empty)

    duplicate = tmp_path / "duplicate.jsonl"
    row = DATASET.read_text(encoding="utf-8").splitlines()[0]
    duplicate.write_text(f"{row}\n{row}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be unique"):
        load_evaluation_cases(duplicate)


def test_invoke_chat_parses_text_and_citations() -> None:
    body = (
        'event: delta\ndata: {"text":"Grounded answer"}\n\n'
        'event: citations\ndata: {"sources":[{"id":"policy","title":"Policy",'
        '"url":"https://support.contoso.example/policy"}]}\n\n'
        'event: done\ndata: {"session_id":"session"}\n\n'
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body, request=request))
    with httpx.Client(transport=transport) as client:
        result = invoke_chat(
            client,
            base_url="https://app.example/",
            token="token",
            query="question",
        )

    assert result.response == "Grounded answer"
    assert result.citations[0].id == "policy"


def test_invoke_chat_rejects_error_and_invalid_citation_events() -> None:
    error_transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text='event: error\ndata: {"message":"failed"}\n\n',
            request=request,
        )
    )
    with (
        httpx.Client(transport=error_transport) as client,
        pytest.raises(EvaluationInvocationError, match="failed"),
    ):
        invoke_chat(client, base_url="https://app.example", token="token", query="question")

    invalid_transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text='event: citations\ndata: {"sources":"invalid"}\n\n',
            request=request,
        )
    )
    with (
        httpx.Client(transport=invalid_transport) as client,
        pytest.raises(EvaluationInvocationError, match="source list"),
    ):
        invoke_chat(client, base_url="https://app.example", token="token", query="question")


def test_evaluate_case_reports_failed_phrases_and_sources() -> None:
    case = EvaluationCase(
        id="case",
        category="test",
        query="query",
        expected_behavior="behavior",
        expected_sources=["expected"],
        required_phrases=["required"],
        forbidden_phrases=["forbidden"],
    )
    result = evaluate_case(
        case,
        InvocationResult(response="forbidden response", citations=[]),
    )

    assert not result.passed
    assert {check.name for check in result.checks if not check.passed} == {
        "expected_sources",
        "required_phrases",
        "forbidden_phrases",
    }


def test_run_local_evaluation_writes_summary_and_cloud_dataset(tmp_path: Path) -> None:
    cases = load_evaluation_cases(DATASET)
    by_query = {case.query: case for case in cases}

    def fake_invoke(
        client: httpx.Client,
        *,
        base_url: str,
        token: str,
        query: str,
    ) -> InvocationResult:
        del client, base_url, token
        case = by_query[query]
        return InvocationResult(
            response=" ".join(case.required_phrases) or "supported response",
            citations=[
                Citation(
                    id=source,
                    title=source,
                    url=f"https://support.contoso.example/{source}",
                )
                for source in case.expected_sources
            ],
        )

    output = tmp_path / "local-evaluation.json"
    with patch("support_assistant.evaluation.local.invoke_chat", side_effect=fake_invoke):
        summary = run_local_evaluation(
            base_url="https://app.example",
            token="token",
            dataset_path=DATASET,
            knowledge_base_path=KNOWLEDGE,
            output_path=output,
        )

    assert summary.failed == 0
    assert summary.pass_rate == 1
    assert output.is_file()
    assert Path(summary.prepared_cloud_dataset).is_file()
    assert '"context":' in Path(summary.prepared_cloud_dataset).read_text(encoding="utf-8")


def _cloud_clients(status: str = "completed") -> tuple[MagicMock, MagicMock]:
    project = MagicMock()
    project.__enter__.return_value = project
    project.datasets.upload_file.return_value = SimpleNamespace(id="dataset-id")
    openai = MagicMock()
    openai.__enter__.return_value = openai
    project.get_openai_client.return_value = openai
    openai.evals.create.return_value = SimpleNamespace(id="eval-id")
    openai.evals.runs.create.return_value = SimpleNamespace(
        id="run-id",
        status=status,
        report_url="https://ai.azure.com/report",
    )
    openai.evals.runs.output_items.list.return_value = [
        SimpleNamespace(model_dump=lambda **_: {"score": 5})
    ]
    return project, openai


def test_cloud_evaluation_writes_results(tmp_path: Path) -> None:
    dataset = tmp_path / "prepared.jsonl"
    dataset.write_text(
        '{"query":"q","response":"r","context":"c","ground_truth":"g"}\n',
        encoding="utf-8",
    )
    output = tmp_path / "cloud.json"
    project, openai = _cloud_clients()
    with patch(
        "support_assistant.evaluation.cloud.AIProjectClient",
        return_value=project,
    ):
        result = run_cloud_evaluation(
            project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            judge_model="judge",
            dataset_path=dataset,
            output_path=output,
            credential=MagicMock(),
        )

    assert result["status"] == "completed"
    assert output.is_file()
    openai.evals.runs.output_items.list.assert_called_once()


@pytest.mark.parametrize("status", ["failed", "canceled"])
def test_cloud_evaluation_reports_terminal_failure(tmp_path: Path, status: str) -> None:
    dataset = tmp_path / "prepared.jsonl"
    dataset.write_text("{}\n", encoding="utf-8")
    project, _ = _cloud_clients(status)
    with (
        patch(
            "support_assistant.evaluation.cloud.AIProjectClient",
            return_value=project,
        ),
        pytest.raises(CloudEvaluationError, match=status),
    ):
        run_cloud_evaluation(
            project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            judge_model="judge",
            dataset_path=dataset,
            output_path=tmp_path / "cloud.json",
            credential=MagicMock(),
        )


def test_cloud_evaluation_timeout_and_azure_errors_are_reported(tmp_path: Path) -> None:
    dataset = tmp_path / "prepared.jsonl"
    dataset.write_text("{}\n", encoding="utf-8")
    project, _ = _cloud_clients("queued")
    with (
        patch(
            "support_assistant.evaluation.cloud.AIProjectClient",
            return_value=project,
        ),
        pytest.raises(CloudEvaluationError, match="timed out"),
    ):
        run_cloud_evaluation(
            project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            judge_model="judge",
            dataset_path=dataset,
            output_path=tmp_path / "cloud.json",
            credential=MagicMock(),
            timeout_seconds=0,
            poll_seconds=0,
        )

    with (
        patch(
            "support_assistant.evaluation.cloud.AIProjectClient",
            side_effect=HttpResponseError("failed"),
        ),
        pytest.raises(CloudEvaluationError, match="cloud evaluation failed"),
    ):
        run_cloud_evaluation(
            project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            judge_model="judge",
            dataset_path=dataset,
            output_path=tmp_path / "cloud.json",
            credential=MagicMock(),
        )


def test_cloud_criteria_and_json_fallback() -> None:
    criteria = _criteria("judge")

    assert {criterion["name"] for criterion in criteria} == {
        "relevance",
        "groundedness",
        "task_adherence",
        "intent_resolution",
        "violence",
        "indirect_attack",
    }
    by_name = {criterion["name"]: criterion for criterion in criteria}
    assert by_name["task_adherence"]["initialization_parameters"] == {"deployment_name": "judge"}
    assert by_name["relevance"]["initialization_parameters"] == {"model": "judge"}
    assert _json_value(object()).startswith("<object object")
