"""Embeddings generated through the Microsoft Foundry project endpoint."""

import asyncio
from typing import Protocol

from azure.ai.projects import AIProjectClient
from azure.core.credentials import TokenCredential
from openai import OpenAIError

from support_assistant.retrieval.provider import RetrievalError


class EmbeddingProvider(Protocol):
    """Generate vectors for search indexing and hybrid queries."""

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return one vector for each input string."""
        ...

    async def close(self) -> None:
        """Release provider resources."""
        ...


class FoundryEmbeddingProvider:
    """Call the project-scoped OpenAI-compatible embeddings API."""

    def __init__(self, *, endpoint: str, model: str, credential: TokenCredential) -> None:
        self._model = model
        self._project_client = AIProjectClient(endpoint=endpoint, credential=credential)
        self._openai_client = self._project_client.get_openai_client()

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await asyncio.to_thread(
                self._openai_client.embeddings.create,
                input=texts,
                model=self._model,
            )
        except (OpenAIError, TimeoutError) as exc:
            raise RetrievalError("Microsoft Foundry could not generate embeddings") from exc

        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]

    async def close(self) -> None:
        await asyncio.to_thread(self._project_client.close)
