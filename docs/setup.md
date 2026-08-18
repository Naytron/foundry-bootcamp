# Setup

Use the dev container when possible. It keeps the workshop on Python 3.12 even when the host has a newer interpreter that Azure or Agent Framework packages do not yet support.

## Prerequisites

- Git
- Python 3.12
- Docker Desktop or another Docker-compatible engine
- Azure CLI
- Azure Developer CLI
- An Azure subscription only when you begin the cloud path
- Permission to create resources and role assignments in the selected subscription

The [Microsoft Foundry prerequisites](https://learn.microsoft.com/azure/foundry/agents/quickstarts/responses-api#prerequisites) describe the current platform requirements.

## Option 1: Dev container or Codespaces

1. Open the repository in a dev-container-compatible editor or create a Codespace.
2. Wait for the post-create dependency installation to finish.
3. Copy `.env.example` to `.env`.
4. Keep `USE_MOCK_SERVICES=true`.
5. Run `python -m support_assistant`.

Open `http://localhost:8000`.

## Option 2: Local Python

### PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m support_assistant
```

### Bash

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
python -m support_assistant
```

Use `local-development-token` in the browser while mock mode is enabled.

## Validate local setup

```bash
ruff check .
ruff format --check .
mypy src
python -m pytest
```

The local path must pass without Azure credentials or network calls.

## Prepare for Azure

1. Sign in with `az login` and `azd auth login`.
2. Run `./scripts/preflight.sh` or `.\scripts\preflight.ps1`.
3. Review [costs](costs.md).
4. Create an `azd` environment and set a unique bootcamp access token.
5. Follow the cloud setup in [Day 1](../labs/day-1/README.md).

After provisioning, use `scripts/run_with_azd_env.py` to run seed, smoke, or evaluation commands with the selected environment values. The wrapper parses `azd` JSON output and never evaluates shell text.

Never add `.env`, `.azure` environment state, tokens, subscription IDs, or tenant IDs to a commit.
