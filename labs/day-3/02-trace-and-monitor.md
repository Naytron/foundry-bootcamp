# Lab 3.2: Trace and Monitor the Application

## Objective

Collect operational evidence across HTTP, retrieval, model, and tool execution without exposing message content by default.

## Inspect configuration

Open:

- `src/support_assistant/observability.py`
- `src/support_assistant/api/routes.py`
- `infra/main.bicep`

The app:

- Enables GenAI tracing instrumentation.
- Exports through the Application Insights connection string.
- Records request ID, session ID, and source count.
- Sets `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false`.
- Rejects content capture in production settings.

Read [client-side tracing for Foundry agents](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-client-side).

## Generate a trace

Invoke a grounded question and a tool question. In Foundry and Application Insights, locate:

- Incoming HTTP request
- Retrieval dependency
- Model invocation
- Tool call
- Streaming span
- Correlated request ID

Do not enable content capture in a shared or production environment.

## Verify

- No user message, token, or tool argument appears in ordinary logs.
- Failed provider calls set an error status but return a safe browser message.
- Container platform logs and application traces are both available.
- The Foundry monitoring dashboard shows token, latency, and failure signals after ingestion.

## Knowledge check

1. Why are Container Apps console logs insufficient for model latency analysis?
2. What does `traceparent` provide across services?
3. When might content recording be justified, and which approvals would be required?

