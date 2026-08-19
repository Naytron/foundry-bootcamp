# Troubleshooting

Start with the local mock path. If it fails, fix the application before investigating Azure.

## Local application

| Symptom | Check |
|---------|-------|
| Python version is rejected | Use Python 3.12 or the dev container |
| Import error | Activate the virtual environment and reinstall `.[dev]` |
| Package TLS or proxy failure | Set an approved `UV_INDEX_URL`, or configure the documented offline `UV_FIND_LINKS` path before rebuilding the dev container |
| HTTP 401 from `/api/chat` | Match the browser bearer token to `BOOTCAMP_ACCESS_TOKEN` |
| HTTP 429 | Wait for the configured rate window or restart the local process |
| UI loads but chat does not | Inspect `/api/config`, browser console, and the SSE response |
| Knowledge directory missing | Run from the repository root or set `KNOWLEDGE_BASE_PATH` |
| Evaluation fails | Open `.foundry/results/local-evaluation.json` and inspect the failed check |

## Microsoft Foundry

| Symptom | Check |
|---------|-------|
| Authentication failed | Run `az account show`, verify tenant, and sign in again |
| HTTP 403 | Verify the caller has the current Foundry role at project scope |
| Deployment not found | Use the deployment name, not only the catalog model name |
| Capacity error | Select another supported region/SKU or request quota |
| Project endpoint rejected | Use `https://...services.ai.azure.com/api/projects/...` |
| Private network timeout | Run from the approved network and verify private DNS |

## Azure AI Search

| Symptom | Check |
|---------|-------|
| Seeding receives HTTP 403 | The developer needs index-management and data-contributor permissions |
| Runtime query receives HTTP 403 | The Container App identity needs query-only index data access |
| Vector dimension mismatch | Align `EMBEDDING_DIMENSIONS` with the embeddings model |
| Semantic query fails | Verify the semantic configuration name and Search SKU |
| Free SKU deployment fails | The subscription may already have a Free Search service; select Basic and review cost |
| Irrelevant local results | Inspect stop words and token overlap; local retrieval is intentionally simple |

The seeding command retries bounded, exponential delays only when Azure returns HTTP 403 while newly created RBAC assignments propagate. Other failures surface immediately. If all retries end in 403, verify role scope and principal IDs instead of increasing the retry indefinitely.

## Container Apps

| Symptom | Check |
|---------|-------|
| Revision will not activate | Inspect system logs, image pull, secret refs, and health probes |
| Image pull denied | Verify AcrPull and the registry identity link |
| Readiness fails | Verify Foundry/Search configuration and `/ready` behavior |
| Cold first request | Expected when minimum replicas is zero |
| No traces | Verify the Application Insights connection, OpenTelemetry setup, and ingestion delay |

## Safe diagnostics

- Use request IDs to correlate API logs and traces.
- Do not paste tokens, connection strings, subscription IDs, tenant IDs, prompts, or customer data into issues.
- Keep message-content tracing disabled unless an approved development scenario requires it.
- Use AppLens and Azure Monitor for live Azure diagnostics rather than adding broad exception catches or debug responses.
