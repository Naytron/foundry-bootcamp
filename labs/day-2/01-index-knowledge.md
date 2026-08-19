# Lab 2.1: Build the Support Knowledge Index

## Objective

Create a repeatable Azure AI Search index from synthetic Markdown while keeping indexing separate from application startup.

## Inspect the data contract

Open `data/knowledge-base/`. Each document has constrained front matter:

```yaml
id: warranty-policy
title: Hardware Warranty Policy
product: Contoso Trail Devices
source_url: https://support.contoso.example/warranty
updated: 2026-05-01
```

The body becomes searchable content. The index keeps source identity so citations can survive retrieval and generation.

Validate locally:

```bash
python scripts/seed_search.py --dry-run
```

## Inspect the index

Open `src/support_assistant/retrieval/indexing.py` and identify:

- Key and filterable fields
- Searchable content fields
- Semantic configuration
- HNSW vector profile
- Vector dimensions
- Idempotent `create_or_update_index`
- Batch embedding and upload behavior

The script uses Microsoft Entra credentials. It never accepts a Search admin key.

## Seed Azure AI Search

> **Azure extension.** Skip this section on the local-only track. If you are deploying the included infrastructure, run this only after `azd up` in Day 3 Lab 3.4.

With existing Azure resources configured in `.env`:

```bash
python scripts/seed_search.py
```

The configured identity needs permission to manage the index and upload documents. The running Container App needs only query access.

Expected output: `Indexed 5 synthetic support documents.`

Read [Azure AI Search with Agent Framework](https://learn.microsoft.com/agent-framework/integrations/by-component/context-providers/azure-ai-search) for the current integration options.

## Verify

- The script reports five indexed documents.
- The index contains a semantic configuration named `support-semantic-config`.
- The vector field dimension matches the selected embeddings deployment.
- Rerunning the script updates rather than duplicates documents.

## Recovery

- Vector dimension error: align `EMBEDDING_DIMENSIONS` with the embeddings deployment.
- HTTP 403: distinguish index-management permission from query permission.
- Semantic configuration error: verify the selected Search SKU supports the requested feature.
- Free SKU conflict: reuse an allowed service or set the Bicep Search SKU parameter to Basic, then review cost.

## Knowledge check

1. Why is the document ID both the Search key and citation identifier?
2. Why is indexing not performed automatically during API startup?
3. Which Search permissions should the runtime identity not have?
