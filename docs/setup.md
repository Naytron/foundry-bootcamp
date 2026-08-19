# Setup

Use the dev container when possible. It keeps the workshop on Python 3.12 even when the host has a newer interpreter that Azure or Agent Framework packages do not yet support.

## Get the repository

```bash
git clone https://github.com/naytron/foundry-bootcamp.git
cd foundry-bootcamp
git switch -c learner/my-name
```

Stay on this learner branch. Do not check out the checkpoint tags while following the labs; use [Checkpoint guide](checkpoints.md) to compare snapshots without losing the current instructions.

## Prerequisites

- Git
- Python 3.12
- Docker Desktop or another Docker-compatible engine
- A dev-container-compatible editor, or Azure CLI and Azure Developer CLI for the Azure tracks
- An Azure subscription only when you begin the cloud path
- Permission to create resources and role assignments in the selected subscription

The [Microsoft Foundry prerequisites](https://learn.microsoft.com/azure/foundry/agents/quickstarts/responses-api#prerequisites) describe the current platform requirements.

## Option 1: Dev container or Codespaces

1. Open the cloned folder in Visual Studio Code.
2. Run **Dev Containers: Reopen in Container** from the command palette. Alternatively, open a [GitHub Codespace](https://codespaces.new/naytron/foundry-bootcamp).
3. Wait until the terminal shows that the post-create dependency installation completed.
4. Run:

   ```bash
   cp .env.example .env
   python -m support_assistant
   ```

5. Open the forwarded port or `http://localhost:8000`.
6. Enter `local-development-token` in **Workshop access**.

### Enterprise package mirrors

If your network blocks `files.pythonhosted.org`, set an approved mirror in the host environment before reopening the container:

```bash
UV_INDEX_URL=https://your-approved-python-mirror/simple
```

For a disconnected workshop, an administrator can provide a complete wheel directory and set `UV_FIND_LINKS`. Set `UV_INSECURE_HOST` only for an explicitly approved HTTP mirror. The post-create script switches to no-index mode when `UV_FIND_LINKS` is present.

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

## Confirm the first run

In another terminal:

```bash
curl --fail http://localhost:8000/health
```

Expected JSON includes `"status":"healthy"` and `"mode":"mock"`. Stop the app with `Ctrl+C` after testing.

## Validate local setup

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
```

The local path must pass without Azure credentials or network calls.

## Prepare for Azure

Skip this section on the local-only track.

1. Review [costs](costs.md).
2. Sign in with `az login` and `azd auth login`.
3. Decide whether to use existing resources (Day 1 Lab 1.3) or deploy the included infrastructure (Day 3 Lab 3.4).
4. Follow that lab's environment and preflight sequence exactly.

After provisioning, use `scripts/run_with_azd_env.py` to run seed, smoke, or evaluation commands with the selected environment values. The wrapper parses `azd` JSON output and never evaluates shell text.

Never add `.env`, `.azure` environment state, tokens, subscription IDs, or tenant IDs to a commit.
