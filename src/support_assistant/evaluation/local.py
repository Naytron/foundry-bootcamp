"""Deterministic evaluation runner for local and deployed workshop endpoints."""

import json
from pathlib import Path

import httpx

from support_assistant.evaluation.models import (
    CaseResult,
    CheckResult,
    Citation,
    EvaluationCase,
    EvaluationSummary,
    InvocationResult,
)
from support_assistant.retrieval.local import load_knowledge_documents


class EvaluationInvocationError(RuntimeError):
    """Raised when the chat API emits an error event."""


def load_evaluation_cases(path: Path) -> list[EvaluationCase]:
    """Load and validate versioned JSONL evaluation cases."""
    cases = [
        EvaluationCase.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise ValueError(f"No evaluation cases found in {path}")
    identifiers = [case.id for case in cases]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Evaluation case IDs must be unique")
    return cases


def invoke_chat(
    client: httpx.Client,
    *,
    base_url: str,
    token: str,
    query: str,
) -> InvocationResult:
    """Invoke the SSE endpoint and extract response text and structured citations."""
    response = client.post(
        f"{base_url.rstrip('/')}/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": query},
    )
    response.raise_for_status()

    text_parts: list[str] = []
    citations: list[Citation] = []
    for name, data in _parse_sse(response.text):
        if name == "delta":
            text_parts.append(str(data["text"]))
        elif name == "citations":
            source_items = data.get("sources")
            if not isinstance(source_items, list):
                raise EvaluationInvocationError("Citation event did not contain a source list")
            citations.extend(Citation.model_validate(item) for item in source_items)
        elif name == "error":
            raise EvaluationInvocationError(str(data["message"]))
    return InvocationResult(response="".join(text_parts).strip(), citations=citations)


def _parse_sse(payload: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in payload.replace("\r\n", "\n").strip().split("\n\n"):
        name = "message"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if data_lines:
            events.append((name, json.loads("\n".join(data_lines))))
    return events


def evaluate_case(case: EvaluationCase, invocation: InvocationResult) -> CaseResult:
    """Apply citation, required-phrase, and forbidden-phrase checks."""
    response = invocation.response.casefold()
    actual_sources = {citation.id for citation in invocation.citations}
    expected_sources = set(case.expected_sources)
    sources_passed = expected_sources <= actual_sources if expected_sources else not actual_sources

    checks = [
        CheckResult(
            name="expected_sources",
            passed=sources_passed,
            detail=(f"expected={sorted(expected_sources)} actual={sorted(actual_sources)}"),
        ),
        CheckResult(
            name="required_phrases",
            passed=all(phrase.casefold() in response for phrase in case.required_phrases),
            detail=f"required={case.required_phrases}",
        ),
        CheckResult(
            name="forbidden_phrases",
            passed=all(phrase.casefold() not in response for phrase in case.forbidden_phrases),
            detail=f"forbidden={case.forbidden_phrases}",
        ),
    ]
    return CaseResult(
        id=case.id,
        category=case.category,
        query=case.query,
        response=invocation.response,
        citations=invocation.citations,
        checks=checks,
        passed=all(check.passed for check in checks),
    )


def run_local_evaluation(
    *,
    base_url: str,
    token: str,
    dataset_path: Path,
    knowledge_base_path: Path,
    output_path: Path,
) -> EvaluationSummary:
    """Invoke all cases, write local results, and prepare a cloud-evaluation dataset."""
    cases = load_evaluation_cases(dataset_path)
    knowledge = {
        document.id: document for document in load_knowledge_documents(knowledge_base_path)
    }

    with httpx.Client(timeout=60.0) as client:
        results = [
            evaluate_case(
                case,
                invoke_chat(client, base_url=base_url, token=token, query=case.query),
            )
            for case in cases
        ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cloud_dataset = output_path.with_name("prepared-cloud-evaluation.jsonl")
    cloud_lines = []
    for case, result in zip(cases, results, strict=True):
        context = "\n\n".join(
            knowledge[citation.id].content
            for citation in result.citations
            if citation.id in knowledge
        )
        cloud_lines.append(
            json.dumps(
                {
                    "query": case.query,
                    "response": result.response,
                    "context": context,
                    "ground_truth": case.expected_behavior,
                },
                separators=(",", ":"),
            )
        )
    cloud_dataset.write_text("\n".join(cloud_lines) + "\n", encoding="utf-8")

    passed = sum(result.passed for result in results)
    summary = EvaluationSummary(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        pass_rate=passed / len(results),
        results=results,
        prepared_cloud_dataset=str(cloud_dataset),
    )
    output_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return summary
