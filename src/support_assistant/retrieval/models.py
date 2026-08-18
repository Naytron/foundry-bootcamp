"""Knowledge document models shared by local and Azure retrieval."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """One source returned by the retrieval layer."""

    id: str
    title: str
    content: str
    product: str
    source_url: str
    updated: str
    score: float = 0.0

    def prompt_block(self) -> str:
        """Render a source as clearly delimited, untrusted reference data."""
        return (
            f"<source id={self.id!r} title={self.title!r}>\n"
            f"{self.content}\n"
            f"Source URL: {self.source_url}\n"
            "</source>"
        )
