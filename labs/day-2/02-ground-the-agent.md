# Lab 2.2: Ground Answers and Render Citations

## Objective

Retrieve relevant support sources before model invocation and preserve their identities through the API and browser.

## Compare local and Azure retrieval

Open:

- `src/support_assistant/retrieval/local.py`
- `src/support_assistant/retrieval/azure_search.py`
- `src/support_assistant/agent/foundry.py`

Local mock mode uses transparent token overlap. It is deterministic and useful for tests, but it is not a substitute for semantic retrieval.

Azure mode:

1. Sends the user query to semantic search.
2. Adds a vector query when `EMBEDDING_MODEL` is configured.
3. Selects only the fields the application needs.
4. Maps Search scores into provider-neutral documents.
5. Delimits retrieved content as untrusted reference data.

## Run locally

Start in mock mode and ask:

```text
Does the warranty cover accidental damage?
```

The answer should reference the hardware warranty policy and the stream should include a `citations` event.

Inspect the browser network response. Notice that citation URLs are validated before links are created and all model output is assigned as text.

## Verify

```bash
python -m pytest tests/test_retrieval.py tests/test_api.py
```

Confirm:

- Warranty content ranks first.
- No-match queries return no fabricated source.
- The API emits source ID, title, and URL as structured data.
- The model prompt labels retrieved content as untrusted.

## Recovery

- Relevant document missing: inspect tokenization locally or Search analyzer/configuration in Azure.
- No citations: verify the retriever returned documents before debugging the model.
- Wrong source link: inspect Search field mapping rather than asking the model to reconstruct URLs.
- Prompt injection followed: stop and complete Lab 2.4 before continuing.

## Knowledge check

1. Why are citations emitted separately from generated text?
2. What does hybrid retrieval add to semantic keyword search?
3. Why is retrieved content context rather than conversational memory?

