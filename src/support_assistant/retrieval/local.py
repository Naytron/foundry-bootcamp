"""Deterministic local retrieval over the synthetic Markdown knowledge base."""

import asyncio
import re
from pathlib import Path

from support_assistant.retrieval.models import KnowledgeDocument

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "with",
}


def load_knowledge_documents(root: Path) -> list[KnowledgeDocument]:
    """Load the workshop's constrained Markdown front matter format."""
    if not root.is_dir():
        raise FileNotFoundError(f"Knowledge-base directory does not exist: {root}")

    documents: list[KnowledgeDocument] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, content = _split_front_matter(text, path)
        documents.append(
            KnowledgeDocument(
                id=metadata["id"],
                title=metadata["title"],
                product=metadata["product"],
                source_url=metadata["source_url"],
                updated=metadata["updated"],
                content=content.strip(),
            )
        )
    if not documents:
        raise ValueError(f"No Markdown documents found in {root}")
    return documents


def _split_front_matter(text: str, path: Path) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path} must start with front matter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path} has unterminated front matter") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or not value.strip():
            raise ValueError(f"{path} contains invalid front matter: {line}")
        metadata[key.strip()] = value.strip()

    required = {"id", "title", "product", "source_url", "updated"}
    missing = required - metadata.keys()
    if missing:
        raise ValueError(f"{path} is missing front matter: {', '.join(sorted(missing))}")
    return metadata, "\n".join(lines[closing + 1 :])


class LocalKnowledgeRetriever:
    """Rank local documents with a transparent token-overlap baseline."""

    def __init__(self, root: Path, *, top_k: int) -> None:
        self._documents = load_knowledge_documents(root)
        self._top_k = top_k

    async def search(self, query: str) -> list[KnowledgeDocument]:
        return await asyncio.to_thread(self._search, query)

    def _search(self, query: str) -> list[KnowledgeDocument]:
        terms = set(TOKEN_PATTERN.findall(query.casefold())) - STOP_WORDS
        if not terms:
            return []

        ranked: list[KnowledgeDocument] = []
        for document in self._documents:
            title_terms = TOKEN_PATTERN.findall(document.title.casefold())
            product_terms = TOKEN_PATTERN.findall(document.product.casefold())
            content_terms = TOKEN_PATTERN.findall(document.content.casefold())
            score = (
                4 * sum(term in terms for term in title_terms)
                + 2 * sum(term in terms for term in product_terms)
                + sum(term in terms for term in content_terms)
            )
            if score:
                ranked.append(
                    KnowledgeDocument(
                        id=document.id,
                        title=document.title,
                        content=document.content,
                        product=document.product,
                        source_url=document.source_url,
                        updated=document.updated,
                        score=float(score),
                    )
                )

        return sorted(ranked, key=lambda item: (-item.score, item.title))[: self._top_k]

    async def close(self) -> None:
        """No resources are held."""
