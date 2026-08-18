# Lab 3.4: Validate, Deploy, and Clean Up

## Objective

Run deployment preflight, inspect the infrastructure, deploy deliberately, verify the user journey, and remove all resources.

## Preflight

1. Review [costs](../../docs/costs.md).
2. Run `scripts/preflight.sh` or `scripts/preflight.ps1`.
3. Confirm subscription, tenant, region, policy, quota, model versions, Search SKU, and role-assignment permission.
4. Inspect `.azure/deployment-plan.md`, `azure.yaml`, and `infra/main.bicep`.
5. Generate a unique workshop token.

Create an environment:

```bash
azd env new
azd env set BOOTCAMP_ACCESS_TOKEN "<unique-generated-value>"
```

Override model or Search parameters with `azd env set` when preflight shows the defaults are unavailable.

## Validate locally

```bash
ruff check .
ruff format --check .
mypy src
python -m pytest
az bicep build --file infra/main.bicep
docker build --tag foundry-bootcamp:local .
```

## Deploy

Only after the checks pass:

```bash
azd up
```

No script or workflow in this repository runs this command automatically.

After provisioning, use the safe command wrapper to supply the selected `azd` environment without shell evaluation:

```bash
python scripts/run_with_azd_env.py python scripts/seed_search.py
```

## Verify

1. Open `SERVICE_URL`.
2. Enter the generated workshop token.
3. Ask the warranty and sensor-pairing questions.
4. Verify structured citations.
5. Run `python scripts/run_with_azd_env.py python scripts/smoke_test.py`.
6. Run the local evaluation suite against `SERVICE_URL`.
7. Inspect Container Apps logs and Foundry traces.

## Clean up

Follow [cleanup](../../docs/cleanup.md). Review the target resource group, then run:

```bash
azd down
```

Confirm the resources are gone before completing the bootcamp.

## Knowledge check

1. Why must model capacity be checked before Bicep deployment?
2. Which identities need Foundry, Search, and ACR roles?
3. What evidence demonstrates that deployment succeeded beyond an HTTP 200 health response?
