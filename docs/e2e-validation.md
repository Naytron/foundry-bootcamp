# End-to-End Validation

This page records learner-focused validation without exposing subscription IDs, tenant IDs, identities, or tokens.

## Scope

- Public fresh-clone journey
- Recommended dev-container setup
- Local-only Day 1-3 path
- Browser UI and API flows
- Deterministic evaluation
- Python, dependency, repository, Bicep, workflow, and production-container checks
- Read-only Azure preflight and provisioning preview
- GitHub Actions CI

No Azure resources are created by this validation.

## Latest result

| Check | Status | Evidence |
|-------|--------|----------|
| Public clone and checkpoint tags | Pass | Fresh clone from `naytron/foundry-bootcamp`; `main` plus all four tags present |
| Dev container setup | Pass | Python 3.12, Azure CLI, azd, Docker-in-Docker, pinned features, and 123 hardened packages |
| Day 1 local journey | Pass | Health, token authentication, streaming chat, session behavior, and focused tests |
| Day 2 local journey | Pass | Five-document schema dry-run, grounding, citations, tools, and prompt-boundary checks |
| Day 3 local journey | Pass | Evaluation, observability tests, repository validation, Bicep, and container path |
| Playwright UI journey | Pass | Page load, token save, streaming response, citations, new chat, invalid-token error, and mobile viewport |
| Deterministic evaluation | Pass | 8/8 cases |
| Static quality and dependency audit | Pass | 109 tests, 95.93% coverage, Ruff, Mypy, and no known vulnerabilities |
| Bicep and production container | Pass | Bicep build/lint; non-root UID 10001; grounded smoke test; no runtime packaging tools |
| External documentation links | Pass | 15/15 locally and in the public workflow |
| Read-only Azure preflight/preview | Pass | Environment helper persisted East US 2, preflight and `azd provision --preview` passed, no resource group appeared, and local state was removed |
| GitHub Actions CI | Pass | Python/repository, Bicep, and production-container jobs green |

Validated: 2026-08-19 against the public `main` branch.

## Defects found and fixed

The clean-room journey found issues that ordinary unit tests did not:

- The root quick start omitted clone, `.env`, and learning-track guidance.
- Local, existing-resource, and deploy-included-infrastructure tracks were mixed together.
- The trust-boundary exercise asked learners to create a document that could not pass the index schema.
- Day 3 environment, preflight, seed, smoke, and evaluation commands were incomplete or out of order.
- Blank optional Azure URLs made a copied `.env.example` invalid in mock mode.
- The dev-container base had a stale Yarn apt source.
- Container-network TLS restrictions needed a documented mirror/offline-wheel path.
- The base container's older `mypy` executable shadowed the pinned project version.
- Root package installation made learner cache paths unwritable.
- Inherited GitPython and setuptools versions failed the dependency audit.
- The mounted repository needed a narrowly scoped Git safe-directory entry.
- Generated tool caches made repository validation slow and noisy.
- Dev Container feature resolution left an untracked lock file.
- The CI smoke-test pipe caused `curl` to exit with a broken-pipe status.
- `azd provision --preview` needed a safe default for first-deployment resource discovery.
- `az account list-locations` could not validate a specified subscription; the helper now resolves subscription context and uses the read-only ARM locations endpoint.
- Preflight overrides could differ from the effective `azd`/process/Bicep deployment location; a synchronization check now blocks mismatches with a repair command.
- Failed environment setup could lose the learner's previous `azd` selection; rollback now restores the exact prior name.
- Workflow redispatch could change region for an existing environment name and orphan a billable stack; tagged environments are now region-bound.

Each issue now has either an automated regression check or a documented, tested setup path.

## Read-only Azure evidence

- All six required resource providers were registered.
- The configured chat and embedding model versions were available in East US 2.
- The subscription had no existing Free Search service.
- The signed-in learner had role-assignment authority.
- Container Apps managed-environment usage was 1 of 50.
- Chat and embedding token quotas exceeded the template's requested capacities.
- Subscription policy assignments did not constrain the workshop resource types or region.
- The provisioning preview completed successfully.
- East US 2 is the environment default, with Sweden Central, North Central US, and East US documented as preflighted override candidates.
- The helper created a temporary local `azd` environment, persisted `eastus2`, generated its token without disclosure, and removed the environment after preview.
- A follow-up existence check confirmed that preview created no resource group.

Subscription, tenant, principal, environment, and token values are intentionally omitted.

## Known validation boundary

This run did not call `azd provision`, `azd up`, or `azd deploy`. It therefore does not claim live validation of model inference, Search indexing, managed-identity propagation, telemetry ingestion, deployed evaluation, or Azure cleanup. Those remain explicitly labeled Azure extensions in the learner guide.

The test network blocked direct TLS access to `files.pythonhosted.org` from containers. The documented `UV_FIND_LINKS` offline-mirror path and Docker build arguments were used and passed. Public GitHub-hosted CI also built the image successfully from the normal package index path.

## Learner usability rubric

Every lab must provide:

1. An objective.
2. Clear local-only or Azure-extension scope.
3. Copy-pasteable commands.
4. Expected results.
5. Verification steps.
6. Recovery guidance where a service or tool can fail.
7. A knowledge check.

The repository validator enforces the structural parts of this rubric. The clean-room journey verifies that the commands work in sequence.
