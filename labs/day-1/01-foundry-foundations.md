# Lab 1.1: Orient to Microsoft Foundry

## Objective

Map the capstone requirements to the current Microsoft Foundry platform before changing code.

## Explore the platform

Read:

1. [What is Microsoft Foundry?](https://learn.microsoft.com/azure/foundry/what-is-foundry)
2. [Build agents using the Responses API](https://learn.microsoft.com/azure/foundry/agents/quickstarts/responses-api)
3. [Microsoft Agent Framework overview](https://learn.microsoft.com/agent-framework/overview/)

Create a short architecture note that answers:

- Which resource groups the project's models, tools, data, and observability?
- Why does this application call the Foundry **project endpoint** instead of a resource-level Azure OpenAI endpoint?
- Why is the agent definition versioned in Python rather than created as a separate prompt-agent resource?
- Which capabilities must be deterministic functions rather than agent decisions?

Compare your notes with [the reference architecture](../../docs/architecture.md).

## Model selection exercise

The capstone needs low latency, streaming, function calling, and grounded support answers. Use the [model choice guide](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/model-choice-guide) and the catalog available in your subscription.

Record:

- Candidate chat model and version
- Candidate embeddings model and version
- Deployment SKU and capacity
- Region availability
- Expected latency and cost trade-off

The repository keeps all model values configurable because availability and quota differ by subscription.

## Verify

You should be able to draw this flow:

```text
Browser -> FastAPI -> Agent Framework -> Foundry project Responses API
                           |
                           +-> Azure AI Search
                           +-> typed support tools
                           +-> OpenTelemetry -> Application Insights
```

## Knowledge check

1. What project-scoped capabilities do you lose when you call only a resource-level model endpoint?
2. When should you use a workflow instead of an agent?
3. Why is a model deployment name configuration rather than source code?

## Stretch

Compare the ephemeral agent pattern used here with Foundry prompt agents and hosted agents. Identify one scenario where each is the better deployment shape.

