# Microsoft Foundry AI Development Bootcamp

Build an enterprise knowledge and support assistant in three self-paced days. The capstone progresses from a first Microsoft Foundry agent to grounded retrieval, tool use, evaluation, observability, and deployment on Azure Container Apps.

> This repository uses synthetic support content and can run locally in mock mode without an Azure subscription. Azure deployment is opt-in and creates billable resources.

## Start here

```bash
git clone https://github.com/naytron/foundry-bootcamp.git
cd foundry-bootcamp
```

Then follow [Setup](docs/setup.md). The recommended path is **Dev Containers: Reopen in Container**, followed by:

```bash
cp .env.example .env
python -m support_assistant
```

Open `http://localhost:8000` and enter `local-development-token`.

## Choose a learning track

| Track | Azure required? | What to complete |
|-------|-----------------|------------------|
| **Local-only** | No | All local sections across Days 1-3; skip sections labeled **Azure extension** |
| **Existing Azure resources** | Yes | Local sections plus Day 1 Lab 1.3 and the Azure extensions in Days 2-3 |
| **Deploy included infrastructure** | Yes, billable | Local sections first, then Day 3 Lab 3.4 |

If you are unsure, use the **local-only** track. It exercises the complete UI, API, grounding contract, tools, and deterministic evaluation without Azure.

## How to use this repository

- Stay on `main` while taking the bootcamp so every lab and reference page remains available.
- Create your own learner branch before making exercise changes: `git switch -c learner/my-name`.
- The checkpoint tags are read-only implementation snapshots for comparison, not the place to read the curriculum.
- See [Checkpoint guide](docs/checkpoints.md) for safe `git show` and `git diff` examples.

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

## Before using Azure

Read [costs](docs/costs.md), run the platform-specific preflight script, and verify subscription policy, model capacity, quota, and role-assignment permissions. The repository never runs `azd up` automatically.

## Reference

- [Architecture](docs/architecture.md)
- [CI/CD](docs/cicd.md)
- [End-to-end validation](docs/e2e-validation.md)
- [Setup](docs/setup.md)
- [Checkpoint guide](docs/checkpoints.md)
- [Glossary](docs/glossary.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Cleanup](docs/cleanup.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

This project is licensed under the [MIT License](LICENSE).
