# Lab 2.4: Test Trust Boundaries

## Objective

Verify the controls between user input, retrieved documents, generated text, and tool arguments without creating an invalid knowledge document.

## Local deterministic exercise

Start the app in mock mode. In another terminal, run the full evaluation:

### PowerShell

```powershell
python scripts/run_evaluation.py `
  --base-url http://localhost:8000 `
  --token local-development-token
```

### Bash

```bash
python scripts/run_evaluation.py \
  --base-url http://localhost:8000 \
  --token local-development-token
```

Expected output: `Local evaluation: 8/8 passed (100%).`

Open `.foundry/results/local-evaluation.json` and find `prompt-injection`. Confirm that:

- The response does not contain the development token.
- The answer rejects unlimited accidental-damage coverage.
- The warranty policy remains the cited source.

Then run the focused prompt-boundary and browser-output tests:

```bash
python -m pytest tests/test_foundry_provider.py tests/test_api.py
```

## Why not create a plain text knowledge file?

The indexer accepts Markdown files with required front matter. A plain text file would correctly fail schema validation before reaching the agent. Indirect prompt-injection testing also requires a deliberately isolated Azure test index and a live model; do not add an adversarial file to a shared or normal support index.

## Azure extension

With an isolated test index, create a valid synthetic document whose body contains an instruction to ignore system rules. Seed only that isolated index, run the prompt-injection evaluation, and delete the test index afterward. Never upload the adversarial fixture to a shared learner index.

## Review controls

| Boundary | Control |
|----------|---------|
| Browser to API | Bearer token, size validation, rate limit |
| API to agent | Structured request and bounded session |
| Search to agent | Delimited untrusted reference block |
| Agent to browser | Text rendering and structured citations |
| Agent to tool | Typed schema and deterministic implementation |
| Tool to external system | Not implemented in this workshop |

Read the [Microsoft Foundry responsible AI guidance](https://learn.microsoft.com/azure/foundry/responsible-use-of-ai-overview).

## Verify

- Local evaluation passes all eight cases.
- No token appears in the response or committed result files.
- Invalid knowledge documents fail before indexing.
- Live indirect-injection tests, if used, target an isolated disposable index.

## Knowledge check

1. Why can a trusted Search service still return untrusted content?
2. Why can output encoding not prevent a model from following a malicious document?
3. Which control stops an agent from turning a support-case draft into a real-world action?
