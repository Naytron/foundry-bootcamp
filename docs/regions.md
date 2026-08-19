# Azure Region Selection

The bootcamp defaults new environments to **East US 2** (`eastus2`).

## Suggested regions

| CLI value | Display name | Notes |
|-----------|--------------|-------|
| `eastus2` | East US 2 | Default and primary workshop recommendation |
| `swedencentral` | Sweden Central | Suggested European alternative |
| `northcentralus` | North Central US | Suggested US alternative |
| `eastus` | East US | Suggested US alternative |

At the latest validation, all four regions exposed the configured `gpt-4.1-mini` (`2025-04-14`) and `text-embedding-3-small` (`1`) model versions and supported Azure Container Apps and Azure AI Search.

Availability, policy, and quota vary by subscription and over time. A suggested region is not a capacity guarantee; always run preflight and preview.

## Create an environment with the default

```bash
python scripts/create_environment.py --subscription <subscription-id>
```

The helper:

- Generates a unique environment name.
- Selects `eastus2`.
- Resolves the signed-in learner's principal.
- Generates and stores a bootcamp access token without printing it.
- Configures only local `azd` environment state.

It does not provision Azure resources.

## Override the region

```bash
python scripts/create_environment.py \
  --subscription <subscription-id> \
  --location swedencentral
```

Replace `swedencentral` with another suggested CLI value. You can also pass another valid Azure location. The helper allows it with a warning; preflight checks the model catalog and provider basics, while you must manually confirm regional service support, policy, and quota before running the provisioning preview.

Preview the resolved values without creating local environment state:

```bash
python scripts/create_environment.py \
  region-preview \
  --subscription <subscription-id> \
  --location northcentralus \
  --principal-id <object-id> \
  --dry-run
```

## Change an existing local environment before provisioning

```bash
azd env set AZURE_LOCATION eastus
python scripts/preflight.py
azd provision --preview --no-prompt
```

Do this only before resources exist.

Changing `AZURE_LOCATION` after provisioning does not move Azure resources. Create a new `azd` environment for the new region, validate it, deploy there, verify the application, and then deliberately clean up the old environment.

## Next steps

After creating or changing an environment:

```bash
python scripts/preflight.py
azd provision --preview --no-prompt
```

Resolve every failure before `azd up`. The tooling never silently selects a fallback region.
