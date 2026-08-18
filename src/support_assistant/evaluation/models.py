"""Typed evaluation inputs and outputs."""

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """One expected behavior from the versioned JSONL dataset."""

    id: str
    category: str
    query: str
    expected_behavior: str
    expected_sources: list[str] = Field(default_factory=list)
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    """One structured source emitted by the chat API."""

    id: str
    title: str
    url: str


class InvocationResult(BaseModel):
    """Response text and citations captured from one SSE stream."""

    response: str
    citations: list[Citation] = Field(default_factory=list)


class CheckResult(BaseModel):
    """One deterministic check applied to a response."""

    name: str
    passed: bool
    detail: str


class CaseResult(BaseModel):
    """All local checks for one evaluation case."""

    id: str
    category: str
    query: str
    response: str
    citations: list[Citation]
    checks: list[CheckResult]
    passed: bool


class EvaluationSummary(BaseModel):
    """Serializable summary for local quality gates."""

    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[CaseResult]
    prepared_cloud_dataset: str
