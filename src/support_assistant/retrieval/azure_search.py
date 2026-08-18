"""Azure AI Search semantic and optional hybrid retrieval."""

import asyncio
from typing import Any

from azure.core.credentials import TokenCredential
from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery, VectorQuery

from support_assistant.retrieval.embeddings import EmbeddingProvider
from support_assistant.retrieval.models import KnowledgeDocument
from support_assistant.retrieval.provider import RetrievalError


class AzureSearchRetriever:
    """Retrieve ranked support sources with Entra-authenticated Azure AI Search."""

    def __init__(
        self,
        *,
        endpoint: str,
        index_name: str,
        semantic_configuration: str,
        vector_field: str,
        credential: TokenCredential,
        top_k: int,
        embeddings: EmbeddingProvider | None = None,
    ) -> None:
        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )
        self._semantic_configuration = semantic_configuration
        self._vector_field = vector_field
        self._top_k = top_k
        self._embeddings = embeddings

    async def search(self, query: str) -> list[KnowledgeDocument]:
        vector: list[float] | None = None
        if self._embeddings:
            vectors = await self._embeddings.embed_many([query])
            vector = vectors[0]
        try:
            return await asyncio.to_thread(self._search, query, vector)
        except (AzureError, TimeoutError) as exc:
            raise RetrievalError("Azure AI Search could not complete the query") from exc

    def _search(self, query: str, vector: list[float] | None) -> list[KnowledgeDocument]:
        vector_queries: list[VectorQuery] | None = None
        if vector:
            vector_queries = [
                VectorizedQuery(
                    vector=vector,
                    k_nearest_neighbors=self._top_k,
                    fields=self._vector_field,
                )
            ]

        results = self._client.search(
            search_text=query,
            query_type="semantic",
            semantic_configuration_name=self._semantic_configuration,
            query_caption="extractive",
            query_caption_highlight_enabled=False,
            vector_queries=vector_queries,
            select=["id", "title", "content", "product", "source_url", "updated"],
            top=self._top_k,
        )
        return [self._to_document(result) for result in results]

    @staticmethod
    def _to_document(result: dict[str, Any]) -> KnowledgeDocument:
        score = result.get("@search.reranker_score") or result.get("@search.score") or 0.0
        return KnowledgeDocument(
            id=str(result["id"]),
            title=str(result["title"]),
            content=str(result["content"]),
            product=str(result["product"]),
            source_url=str(result["source_url"]),
            updated=str(result["updated"]),
            score=float(score),
        )

    async def close(self) -> None:
        await asyncio.to_thread(self._client.close)
        if self._embeddings:
            await self._embeddings.close()
