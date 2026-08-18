# Microsoft Foundry AI Development Bootcamp

Build an enterprise knowledge and support assistant in three self-paced days. The capstone progresses from a first Microsoft Foundry agent to grounded retrieval, tool use, evaluation, observability, and deployment on Azure Container Apps.

> This repository uses synthetic support content and can run locally in mock mode without an Azure subscription. Azure deployment is opt-in and creates billable resources.

## What you will build

- A Python support agent built with Microsoft Agent Framework and the Foundry Responses API.
- A FastAPI backend with streaming chat and a lightweight browser UI.
- Grounded answers from Azure AI Search with source citations.
- Typed warranty and support-case tools with confirmation boundaries.
- Quality, safety, and groundedness evaluations.
- OpenTelemetry traces in Application Insights.
- Repeatable Azure infrastructure through `azd` and Bicep.

## Learning path

| Day | Outcome | Start here |
|-----|---------|------------|
| 1 | Run a first agent and expose it through an API and chat UI | [Day 1](labs/day-1/README.md) |
| 2 | Add enterprise grounding, citations, conversations, and tools | [Day 2](labs/day-2/README.md) |
| 3 | Evaluate, observe, secure, and package the application for Azure | [Day 3](labs/day-3/README.md) |

## Choose your setup

- **Dev container or Codespaces:** recommended; includes Python 3.12, Azure CLI, Azure Developer CLI, and Docker.
- **Local machine:** follow [setup](docs/setup.md) with Python 3.12 and the required Azure tools.
- **No Azure access yet:** use the complete local mock path in Day 1.

## Quick local start

```bash
python -m pip install -e ".[dev]"
python -m uvicorn support_assistant.main:app --reload
```

Open `http://localhost:8000` and use the development token from your local `.env`.

## Before using Azure

Read [costs](docs/costs.md), run the platform-specific preflight script, and verify subscription policy, model capacity, quota, and role-assignment permissions. The repository never runs `azd up` automatically.

## Reference

- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Cleanup](docs/cleanup.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

This project is licensed under the [MIT License](LICENSE).
