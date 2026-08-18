"""Create and populate the workshop Azure AI Search index."""

import asyncio
from pathlib import Path

from azure.core.credentials import TokenCredential
from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from support_assistant.retrieval.embeddings import EmbeddingProvider
from support_assistant.retrieval.local import load_knowledge_documents
from support_assistant.retrieval.provider import RetrievalError


async def seed_search_index(
    *,
    endpoint: str,
    index_name: str,
    semantic_configuration: str,
    vector_field: str,
    vector_dimensions: int,
    knowledge_base_path: str,
    credential: TokenCredential,
    embeddings: EmbeddingProvider,
) -> int:
    """Create the index schema and upload all synthetic knowledge documents."""
    documents = await asyncio.to_thread(load_knowledge_documents, Path(knowledge_base_path))
    vectors = await embeddings.embed_many([document.content for document in documents])
    if len(vectors) != len(documents):
        raise RetrievalError("Embedding response count did not match document count")
    if any(len(vector) != vector_dimensions for vector in vectors):
        raise RetrievalError(
            f"Embedding vectors must contain exactly {vector_dimensions} dimensions"
        )

    index = _build_index(
        name=index_name,
        semantic_configuration=semantic_configuration,
        vector_field=vector_field,
        vector_dimensions=vector_dimensions,
    )
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    try:
        await asyncio.to_thread(index_client.create_or_update_index, index)
        payload = [
            {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "product": document.product,
                "source_url": document.source_url,
                "updated": document.updated,
                vector_field: vector,
            }
            for document, vector in zip(documents, vectors, strict=True)
        ]
        results = await asyncio.to_thread(search_client.merge_or_upload_documents, payload)
    except (AzureError, TimeoutError) as exc:
        raise RetrievalError("Azure AI Search indexing failed") from exc
    finally:
        await asyncio.to_thread(index_client.close)
        await asyncio.to_thread(search_client.close)

    failed = [result.key for result in results if not result.succeeded]
    if failed:
        raise RetrievalError(f"Azure AI Search rejected documents: {', '.join(failed)}")
    return len(results)


def _build_index(
    *,
    name: str,
    semantic_configuration: str,
    vector_field: str,
    vector_dimensions: int,
) -> SearchIndex:
    fields = [
        SimpleField(
            name="id",
            type="Edm.String",
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="title",
            type="Edm.String",
            filterable=True,
            sortable=True,
        ),
        SearchableField(name="content", type="Edm.String"),
        SearchableField(
            name="product",
            type="Edm.String",
            filterable=True,
            facetable=True,
        ),
        SimpleField(name="source_url", type="Edm.String"),
        SimpleField(
            name="updated",
            type="Edm.String",
            filterable=True,
            sortable=True,
        ),
        SearchField(
            name=vector_field,
            type="Collection(Edm.Single)",
            searchable=True,
            vector_search_dimensions=vector_dimensions,
            vector_search_profile_name="support-vector-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="support-hnsw")],
        profiles=[
            VectorSearchProfile(
                name="support-vector-profile",
                algorithm_configuration_name="support-hnsw",
            )
        ],
    )
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=semantic_configuration,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                    keywords_fields=[SemanticField(field_name="product")],
                ),
            )
        ]
    )
    return SearchIndex(
        name=name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )
