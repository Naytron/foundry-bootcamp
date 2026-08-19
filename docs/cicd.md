# CI/CD

The repository separates non-billable pull-request validation from an explicitly dispatched Azure deployment.

## Continuous integration

`.github/workflows/ci.yml` runs:

- Ruff lint and format checks
- Mypy strict type checking
- Pytest with branch coverage
- Python dependency audit
- Synthetic-data and repository integrity checks
- Bicep compilation
- Production container build and mock-mode smoke test

Workflow permissions are read-only, actions are pinned to immutable commit SHAs, and jobs do not receive Azure credentials.

## Optional deployment

`.github/workflows/deploy.yml` runs only through `workflow_dispatch` and targets a protected GitHub environment named `workshop`.

The location input defaults to `eastus2`. A maintainer can override it with another preflighted region when manually dispatching the workflow.

An environment name is bound to its original region after the first deployment. The workflow rejects a different location for an existing tagged environment to prevent creating a second billable stack. Reuse the original location or choose a new environment name.

Configure environment variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_PRINCIPAL_ID` (the service principal object ID, not its application/client ID)

Configure one environment secret:

- `BOOTCAMP_ACCESS_TOKEN`

Azure CLI and Azure Developer CLI both authenticate through GitHub OIDC federation. Do not create or store a client secret.

Protect the environment with required reviewers and restrict which branches can deploy. The workflow validates Bicep, configures an `azd` environment, provisions infrastructure, retries only transient ACR authorization propagation during image deployment, seeds synthetic Search content, and runs a grounded smoke test.

## Quality gates

Cloud evaluation is not part of every pull request because it is billable and requires an Azure identity. Run it manually or add a protected scheduled workflow only after defining:

- Evaluation budget
- Dataset and evaluator ownership
- Pass thresholds
- Failure triage
- Model and prompt rollback
- Data-retention policy

Never make an LLM judge the only production release gate. Combine deterministic checks, built-in evaluators, safety review, and human approval.
