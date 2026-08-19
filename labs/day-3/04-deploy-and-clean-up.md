# Lab 3.4: Validate, Deploy, and Clean Up

## Objective

Validate the completed application locally, then optionally create a deliberate Azure environment, verify it, and remove it.

## Local validation - required for every track

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
python scripts/seed_search.py --dry-run
python scripts/validate_repo.py
az bicep build --file infra/main.bicep
docker build --tag foundry-bootcamp:local .
```

Run the container in mock mode and use `scripts/smoke_test.py`, or rely on the equivalent CI container job. Local-only learners stop here.

## Azure extension - prepare an environment

> This section is billable after `azd up`. Read [costs](../../docs/costs.md) first. The preflight and preview commands do not create resources.

Choose a subscription and a region that supports both configured models. Use a unique environment name and token.

### PowerShell

```powershell
$subscriptionId = "<your-subscription-id>"
$location = "eastus2"
$environmentName = "foundry-bootcamp-$(-join ((97..122) | Get-Random -Count 4 | ForEach-Object {[char]$_}))"
$accessToken = python -c "import secrets; print(secrets.token_urlsafe(32))"
$principalId = az ad signed-in-user show --query id --output tsv

azd env new $environmentName --no-prompt
azd env set AZURE_SUBSCRIPTION_ID $subscriptionId
azd env set AZURE_LOCATION $location
azd env set AZURE_PRINCIPAL_ID $principalId
azd env set AZURE_PRINCIPAL_TYPE User
azd env set BOOTCAMP_ACCESS_TOKEN $accessToken

python scripts/preflight.py --subscription $subscriptionId --location $location
azd provision --preview --no-prompt
```

### Bash

```bash
SUBSCRIPTION_ID="<your-subscription-id>"
LOCATION="eastus2"
ENVIRONMENT_NAME="foundry-bootcamp-$(python -c 'import secrets; print(secrets.token_hex(2))')"
ACCESS_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
PRINCIPAL_ID="$(az ad signed-in-user show --query id --output tsv)"

azd env new "$ENVIRONMENT_NAME" --no-prompt
azd env set AZURE_SUBSCRIPTION_ID "$SUBSCRIPTION_ID"
azd env set AZURE_LOCATION "$LOCATION"
azd env set AZURE_PRINCIPAL_ID "$PRINCIPAL_ID"
azd env set AZURE_PRINCIPAL_TYPE User
azd env set BOOTCAMP_ACCESS_TOKEN "$ACCESS_TOKEN"

python scripts/preflight.py --subscription "$SUBSCRIPTION_ID" --location "$LOCATION"
azd provision --preview --no-prompt
```

Resolve every preflight or preview failure before continuing. Override model, model-version, Search-SKU, or capacity parameters with `azd env set` only after confirming the available values.

## Deploy

Only after local validation and preview pass:

```bash
azd up
```

No workflow runs this command unless a repository maintainer manually dispatches the protected deployment workflow.

## Seed and verify

```bash
python scripts/run_with_azd_env.py python scripts/seed_search.py
python scripts/run_with_azd_env.py python scripts/smoke_test.py
python scripts/run_with_azd_env.py python scripts/run_evaluation.py
```

Expected outcomes:

1. Search reports five indexed synthetic documents.
2. Smoke test passes health and grounded warranty citation checks.
3. Local evaluation reports 8/8 passing cases against `SERVICE_URL`.
4. Container Apps logs and Foundry traces appear after ingestion.

## Clean up

Follow [Cleanup](../../docs/cleanup.md). Review the target resource group, then run:

```bash
azd down
```

Confirm the workshop resource group, model deployments, Search service, registry, Container App, and monitoring resources are gone.

## Verify

- Local quality, Bicep, container, and smoke tests pass.
- Preflight and preview pass before any deployment.
- Azure-only values remain in ignored `azd` environment state.
- Deployed smoke and evaluation checks pass if you use the Azure extension.
- The Azure environment is deleted after the extension.

## Knowledge check

1. Why must model capacity be checked before Bicep deployment?
2. Which identities need Foundry, Search, monitoring, and ACR roles?
3. What evidence demonstrates deployment success beyond an HTTP 200 health response?
