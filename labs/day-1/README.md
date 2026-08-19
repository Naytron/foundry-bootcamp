# Day 1: Build Your First Foundry Agent

Day 1 establishes the capstone architecture, proves the local development path, and connects the application to a Microsoft Foundry project.

**Track guidance:** Labs 1.1 and 1.2 are required for every learner. Lab 1.3 is an **Azure extension** for learners who already have Foundry and Search resources. Learners deploying the included infrastructure wait until Day 3 Lab 3.4.

## Learning objectives

By the end of this day, you can:

- Explain the relationship between a Foundry account, project, model deployment, Responses API, and agent.
- Select a model for a latency-sensitive support scenario.
- Authenticate locally without an API key.
- Run the FastAPI service and browser UI in mock mode.
- Stream a response from Microsoft Agent Framework through the API.
- Distinguish liveness, readiness, and application behavior checks.

## Labs

1. [Orient to Microsoft Foundry](01-foundry-foundations.md)
2. [Run the capstone locally](02-local-agent.md)
3. [Azure extension: connect existing resources](03-foundry-connection.md)

## Day checkpoint

You are complete when:

- `GET /health` and `GET /ready` return HTTP 200.
- The chat UI streams a deterministic answer in mock mode.
- An invalid or missing workshop token receives HTTP 401.
- Local-only: your mock-mode chat and focused tests pass.
- Azure extension: your configuration uses a project endpoint and deployment name rather than an API key.
- All Day 1 tests pass.

Stay on your learner branch. Use the [`day-1-complete` checkpoint](../../docs/checkpoints.md) only for comparison.
