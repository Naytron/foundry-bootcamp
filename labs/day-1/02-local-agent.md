# Lab 1.2: Run the Capstone Locally

## Objective

Run the complete HTTP and browser path without Azure resources so application defects are separated from cloud configuration problems.

## Configure

Follow [setup](../../docs/setup.md), then confirm these values in your uncommitted `.env`:

```dotenv
APP_ENV=development
USE_MOCK_SERVICES=true
BOOTCAMP_ACCESS_TOKEN=local-development-token
```

Start the app:

```bash
python -m support_assistant
```

Open `http://localhost:8000`, enter the local development token, and ask:

```text
How do I reset my password?
```

## Inspect

Trace the request through:

- `src/support_assistant/web/app.js`
- `src/support_assistant/api/routes.py`
- `src/support_assistant/agent/service.py`
- `src/support_assistant/agent/mock.py`

Notice that the browser parses server-sent events and never renders model output as HTML.

## Verify

### PowerShell

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/api/chat `
  -Method Post `
  -Headers @{ Authorization = "Bearer local-development-token" } `
  -ContentType "application/json" `
  -Body '{"message":"Tell me about warranty coverage."}'
```

### Bash

```bash
curl --fail http://localhost:8000/health
curl --no-buffer --fail \
  -H "Authorization: Bearer local-development-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about warranty coverage."}' \
  http://localhost:8000/api/chat
```

Run the automated checks:

```bash
python -m pytest tests/test_api.py tests/test_service.py
```

## Recovery

- HTTP 401: the bearer token does not match `BOOTCAMP_ACCESS_TOKEN`.
- Import error: verify the virtual environment is active and reinstall with the `dev` extra.
- Port in use: set an unused `PORT` in `.env`.
- Blank page: inspect the browser console and verify `/api/config` returns JSON.

## Knowledge check

1. Why are health endpoints not protected by the workshop token?
2. Why does the UI assign response text with `textContent`?
3. What limitations does in-memory conversation state create?

