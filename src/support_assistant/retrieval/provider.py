"""Knowledge-retrieval interfaces and errors."""

from typing import Protocol

from support_assistant.retrieval.models import KnowledgeDocument


class RetrievalError(RuntimeError):
    """Raised when the knowledge source cannot complete a search."""


class KnowledgeRetriever(Protocol):
    """Provider-neutral retrieval contract."""

    async def search(self, query: str) -> list[KnowledgeDocument]:
        """Return the most relevant support documents."""
        ...

    async def close(self) -> None:
        """Release provider resources."""
        ...


class NullKnowledgeRetriever:
    """Return no context before the grounding lab is enabled."""

    async def search(self, query: str) -> list[KnowledgeDocument]:
        del query
        return []

    async def close(self) -> None:
        """No resources are held."""
