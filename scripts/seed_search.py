"""Create and populate the synthetic support index."""

import argparse
import asyncio
from pathlib import Path

from support_assistant.config import Settings
from support_assistant.identity import create_credential
from support_assistant.retrieval.embeddings import FoundryEmbeddingProvider
from support_assistant.retrieval.indexing import seed_search_index
from support_assistant.retrieval.local import load_knowledge_documents


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local documents without calling Azure.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/knowledge-base"),
        help="Directory containing synthetic Markdown documents.",
    )
    return parser.parse_args()


async def _run() -> None:
    args = _arguments()
    documents = load_knowledge_documents(args.data)
    if args.dry_run:
        print(f"Validated {len(documents)} knowledge documents in {args.data}.")
        return

    settings = Settings()
    if not settings.foundry_project_endpoint:
        raise SystemExit("FOUNDRY_PROJECT_ENDPOINT is required")
    if not settings.embedding_model:
        raise SystemExit("EMBEDDING_MODEL is required")
    if not settings.azure_ai_search_endpoint:
        raise SystemExit("AZURE_AI_SEARCH_ENDPOINT is required")

    credential = create_credential(settings)
    embeddings = FoundryEmbeddingProvider(
        endpoint=str(settings.foundry_project_endpoint).rstrip("/"),
        model=settings.embedding_model,
        credential=credential,
    )
    try:
        count = await seed_search_index(
            endpoint=str(settings.azure_ai_search_endpoint).rstrip("/"),
            index_name=settings.azure_ai_search_index,
            semantic_configuration=settings.azure_ai_search_semantic_configuration,
            vector_field=settings.azure_ai_search_vector_field,
            vector_dimensions=settings.embedding_dimensions,
            knowledge_base_path=str(args.data),
            credential=credential,
            embeddings=embeddings,
        )
    finally:
        await embeddings.close()
        credential.close()

    print(f"Indexed {count} synthetic support documents.")


if __name__ == "__main__":
    asyncio.run(_run())
