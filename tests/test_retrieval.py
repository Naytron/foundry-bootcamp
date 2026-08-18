"""Knowledge retrieval, embeddings, and indexing tests."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError
from openai import OpenAIError

from support_assistant.retrieval.azure_search import AzureSearchRetriever
from support_assistant.retrieval.embeddings import FoundryEmbeddingProvider
from support_assistant.retrieval.indexing import _build_index, seed_search_index
from support_assistant.retrieval.local import LocalKnowledgeRetriever, load_knowledge_documents
from support_assistant.retrieval.models import KnowledgeDocument
from support_assistant.retrieval.provider import NullKnowledgeRetriever, RetrievalError

KNOWLEDGE_ROOT = Path("data/knowledge-base")


class FakeEmbeddings:
    """Return one deterministic three-dimensional vector per input."""

    def __init__(self) -> None:
        self.closed = False

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), 0.5, 1.0] for index, _ in enumerate(texts)]

    async def close(self) -> None:
        self.closed = True


def _document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id="warranty-policy",
        title="Hardware Warranty Policy",
        content="The limited hardware warranty lasts two years.",
        product="Contoso Trail Devices",
        source_url="https://support.contoso.example/warranty",
        updated="2026-05-01",
        score=2.0,
    )


def test_loads_synthetic_knowledge_documents() -> None:
    documents = load_knowledge_documents(KNOWLEDGE_ROOT)

    assert len(documents) == 5
    assert {document.id for document in documents} >= {"warranty-policy", "account-access"}


async def test_local_retrieval_ranks_relevant_document() -> None:
    retriever = LocalKnowledgeRetriever(KNOWLEDGE_ROOT, top_k=2)

    results = await retriever.search("Is accidental damage covered by the warranty?")
    await retriever.close()

    assert results[0].id == "warranty-policy"
    assert results[0].score > 0


async def test_local_retrieval_returns_empty_for_no_terms() -> None:
    retriever = LocalKnowledgeRetriever(KNOWLEDGE_ROOT, top_k=2)

    assert await retriever.search("!!!") == []


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("No front matter", "must start with front matter"),
        ("---\nid: test\n", "unterminated front matter"),
        ("---\nid test\n---\nBody", "invalid front matter"),
        ("---\nid: test\n---\nBody", "missing front matter"),
    ],
)
def test_invalid_front_matter_is_reported(tmp_path: Path, content: str, message: str) -> None:
    (tmp_path / "bad.md").write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_knowledge_documents(tmp_path)


def test_empty_knowledge_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No Markdown documents"):
        load_knowledge_documents(tmp_path)


def test_missing_knowledge_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_knowledge_documents(tmp_path / "missing")


def test_prompt_block_marks_source_boundaries() -> None:
    block = _document().prompt_block()

    assert "<source" in block
    assert "warranty-policy" in block
    assert block.endswith("</source>")


async def test_null_retriever_returns_no_context() -> None:
    retriever = NullKnowledgeRetriever()

    assert await retriever.search("question") == []
    await retriever.close()


async def test_azure_search_uses_semantic_and_vector_queries() -> None:
    embeddings = FakeEmbeddings()
    result = {
        "id": "warranty-policy",
        "title": "Warranty",
        "content": "Two years.",
        "product": "Trail Sensor",
        "source_url": "https://support.contoso.example/warranty",
        "updated": "2026-05-01",
        "@search.reranker_score": 3.5,
    }
    with patch("support_assistant.retrieval.azure_search.SearchClient") as client_type:
        client_type.return_value.search.return_value = [result]
        retriever = AzureSearchRetriever(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            credential=MagicMock(),
            top_k=3,
            embeddings=embeddings,
        )

        documents = await retriever.search("warranty")
        await retriever.close()

    assert documents[0].score == 3.5
    kwargs = client_type.return_value.search.call_args.kwargs
    assert kwargs["query_type"] == "semantic"
    assert kwargs["vector_queries"][0].fields == "content_vector"
    assert embeddings.closed
    client_type.return_value.close.assert_called_once()


async def test_azure_search_maps_service_errors() -> None:
    with patch("support_assistant.retrieval.azure_search.SearchClient") as client_type:
        client_type.return_value.search.side_effect = HttpResponseError("search failed")
        retriever = AzureSearchRetriever(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            credential=MagicMock(),
            top_k=3,
        )

        with pytest.raises(RetrievalError, match="could not complete"):
            await retriever.search("warranty")


async def test_foundry_embeddings_preserve_response_order() -> None:
    response = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[2.0, 2.0]),
            SimpleNamespace(index=0, embedding=[1.0, 1.0]),
        ]
    )
    project = MagicMock()
    project.get_openai_client.return_value.embeddings.create.return_value = response
    with patch(
        "support_assistant.retrieval.embeddings.AIProjectClient",
        return_value=project,
    ):
        provider = FoundryEmbeddingProvider(
            endpoint="https://example.services.ai.azure.com/api/projects/demo",
            model="embedding",
            credential=MagicMock(),
        )
        vectors = await provider.embed_many(["one", "two"])
        await provider.close()

    assert vectors == [[1.0, 1.0], [2.0, 2.0]]
    project.get_openai_client.return_value.close.assert_called_once()
    project.close.assert_called_once()


async def test_foundry_embedding_errors_are_sanitized() -> None:
    project = MagicMock()
    project.get_openai_client.return_value.embeddings.create.side_effect = OpenAIError("failed")
    with patch(
        "support_assistant.retrieval.embeddings.AIProjectClient",
        return_value=project,
    ):
        provider = FoundryEmbeddingProvider(
            endpoint="https://example.services.ai.azure.com/api/projects/demo",
            model="embedding",
            credential=MagicMock(),
        )
        with pytest.raises(RetrievalError, match="could not generate"):
            await provider.embed_many(["one"])


def test_index_schema_contains_semantic_and_vector_configuration() -> None:
    index = _build_index(
        name="support",
        semantic_configuration="semantic",
        vector_field="content_vector",
        vector_dimensions=3,
    )

    assert index.name == "support"
    assert index.vector_search.profiles[0].name == "support-vector-profile"
    assert index.semantic_search.configurations[0].name == "semantic"


async def test_seed_search_index_uploads_documents() -> None:
    embeddings = FakeEmbeddings()
    success = SimpleNamespace(key="warranty-policy", succeeded=True)
    with (
        patch(
            "support_assistant.retrieval.indexing.load_knowledge_documents",
            return_value=[_document()],
        ),
        patch("support_assistant.retrieval.indexing.SearchIndexClient") as index_client,
        patch("support_assistant.retrieval.indexing.SearchClient") as search_client,
    ):
        search_client.return_value.merge_or_upload_documents.return_value = [success]
        count = await seed_search_index(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            vector_dimensions=3,
            knowledge_base_path="data",
            credential=MagicMock(),
            embeddings=embeddings,
        )

    assert count == 1
    index_client.return_value.create_or_update_index.assert_called_once()
    search_client.return_value.merge_or_upload_documents.assert_called_once()
    index_client.return_value.close.assert_called_once()
    search_client.return_value.close.assert_called_once()


async def test_seed_search_index_rejects_dimension_mismatch() -> None:
    with (
        patch(
            "support_assistant.retrieval.indexing.load_knowledge_documents",
            return_value=[_document()],
        ),
        pytest.raises(RetrievalError, match="exactly 4 dimensions"),
    ):
        await seed_search_index(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            vector_dimensions=4,
            knowledge_base_path="data",
            credential=MagicMock(),
            embeddings=FakeEmbeddings(),
        )


async def test_seed_search_index_reports_rejected_documents() -> None:
    rejected = SimpleNamespace(key="warranty-policy", succeeded=False)
    with (
        patch(
            "support_assistant.retrieval.indexing.load_knowledge_documents",
            return_value=[_document()],
        ),
        patch("support_assistant.retrieval.indexing.SearchIndexClient"),
        patch("support_assistant.retrieval.indexing.SearchClient") as search_client,
    ):
        search_client.return_value.merge_or_upload_documents.return_value = [rejected]
        with pytest.raises(RetrievalError, match="rejected documents"):
            await seed_search_index(
                endpoint="https://example.search.windows.net",
                index_name="support",
                semantic_configuration="semantic",
                vector_field="content_vector",
                vector_dimensions=3,
                knowledge_base_path="data",
                credential=MagicMock(),
                embeddings=FakeEmbeddings(),
            )


async def test_seed_search_index_retries_rbac_propagation(tmp_path: Path) -> None:
    response = MagicMock(status_code=403)
    forbidden = HttpResponseError("role assignment is propagating", response=response)
    wrapped = RetrievalError("indexing failed")
    wrapped.__cause__ = forbidden

    with (
        patch(
            "support_assistant.retrieval.indexing._seed_search_index_once",
            side_effect=[wrapped, 5],
        ) as seed_once,
        patch("support_assistant.retrieval.indexing.asyncio.sleep") as sleep,
    ):
        count = await seed_search_index(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            vector_dimensions=3,
            knowledge_base_path=str(tmp_path),
            credential=MagicMock(),
            embeddings=FakeEmbeddings(),
            rbac_retry_attempts=2,
            rbac_retry_initial_seconds=0.25,
        )

    assert count == 5
    assert seed_once.call_count == 2
    sleep.assert_awaited_once_with(0.25)


async def test_seed_search_index_does_not_retry_non_authorization_error(
    tmp_path: Path,
) -> None:
    error = RetrievalError("schema is invalid")
    with (
        patch(
            "support_assistant.retrieval.indexing._seed_search_index_once",
            side_effect=error,
        ) as seed_once,
        pytest.raises(RetrievalError, match="schema is invalid"),
    ):
        await seed_search_index(
            endpoint="https://example.search.windows.net",
            index_name="support",
            semantic_configuration="semantic",
            vector_field="content_vector",
            vector_dimensions=3,
            knowledge_base_path=str(tmp_path),
            credential=MagicMock(),
            embeddings=FakeEmbeddings(),
            rbac_retry_attempts=8,
        )

    seed_once.assert_called_once()
