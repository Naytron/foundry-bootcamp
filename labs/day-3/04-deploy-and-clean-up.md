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

Choose a subscription. The helper generates a unique environment, defaults to East US 2, resolves your learner principal, and stores a generated access token without printing it:

```bash
python scripts/create_environment.py --subscription <your-subscription-id>
python scripts/preflight.py
azd provision --preview --no-prompt
```

Expected setup output identifies `East US 2 (eastus2, default)` and never prints the access token.

To override the default with a suggested region:

```bash
python scripts/create_environment.py \
  --subscription <your-subscription-id> \
  --location swedencentral
```

See [Azure region selection](../../docs/regions.md) for `northcentralus`, `eastus`, custom-region warnings, dry-run, and migration guidance.

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
