# Lab 1.3: Azure Extension - Connect Existing Resources

> **Optional and Azure-dependent.** Skip this lab on the local-only track. If you plan to deploy this repository's infrastructure, continue to Day 2 in mock mode and return to Azure in Day 3 Lab 3.4.

## Objective

Replace the deterministic mock provider with Microsoft Agent Framework and a Foundry project endpoint while keeping the API contract unchanged.

## Preflight

Do not provision until you have:

1. Read [cost guidance](../../docs/costs.md).
2. Signed in with Azure CLI and Azure Developer CLI.
3. Run the platform-specific preflight script.
4. Confirmed subscription policy, role-assignment permission, region, model capacity, and Search SKU.
5. Generated a unique `BOOTCAMP_ACCESS_TOKEN`.

The infrastructure is intentionally parameterized. Never assume a model is available because it appears in documentation.

## Configure an existing project

If you are not provisioning the included infrastructure, set these values in `.env`:

```dotenv
APP_ENV=development
USE_MOCK_SERVICES=false
FOUNDRY_PROJECT_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com/api/projects/YOUR-PROJECT
FOUNDRY_MODEL=YOUR-CHAT-DEPLOYMENT
EMBEDDING_MODEL=YOUR-EMBEDDING-DEPLOYMENT
AZURE_AI_SEARCH_ENDPOINT=https://YOUR-SEARCH.search.windows.net
AZURE_AI_SEARCH_INDEX=support-knowledge
BOOTCAMP_ACCESS_TOKEN=YOUR-UNIQUE-TOKEN
```

Sign in with `az login`. Local code uses `DefaultAzureCredential`; Azure-hosted code uses `ManagedIdentityCredential`.

## Inspect the adapter

Open `src/support_assistant/agent/foundry.py`.

Confirm that it:

- Uses `FoundryChatClient` with a project endpoint.
- Uses a deployment name from configuration.
- Creates an Agent Framework session for conversation continuity.
- Streams text updates.
- Converts expected Azure transport, authentication, and service failures into a safe application error.

## Run

Start the app and ask a simple, non-grounded question. Day 2 adds private knowledge and citations.

## Verify

- The browser mode badge says **Microsoft Foundry**.
- The response streams through the same `/api/chat` endpoint.
- No API key exists in `.env`, application code, browser storage, or network requests.
- A second message reuses the session ID returned in the first stream.

## Recovery

- Authentication failure: run `az account show` and sign in to the correct tenant.
- HTTP 403: verify the identity has the current Foundry user role at project scope.
- Deployment not found: use the deployment name, not the model catalog name.
- Capacity or quota failure: select another supported region/SKU or request quota before provisioning.
- Network timeout: verify project public access or run from the required private network.

## Knowledge check

1. Why does production use `ManagedIdentityCredential` rather than `DefaultAzureCredential`?
2. Why is the Foundry endpoint kept server-side?
3. Which failures should be returned to learners, and which details should remain only in sanitized logs?
