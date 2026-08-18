# Azure Deployment Plan

> **Status:** Executing

Generated: 2026-08-18

---

## 1. Project Overview

**Goal:** Create a public, self-paced Microsoft Foundry developer bootcamp whose capstone can be deployed to Azure Container Apps.

**Path:** New Project

**Deployment boundary:** Generate and validate deployment artifacts without provisioning Azure resources. Learners select their own subscription, region, model capacity, and policy-compliant settings before running `azd up`.

---

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Development / training |
| Scale | Small, single-region workshop environment |
| Budget | Cost-optimized; scale to zero; cleanup required |
| Subscription | Learner-supplied at deployment time; no subscription is used while building this repository |
| Location | Learner-supplied `AZURE_LOCATION`; preflight verifies model and service availability |
| Compliance | Synthetic data only; no regulated or customer data |
| Architecture preference | Azure Developer CLI with modular Bicep |

### Policy constraints

No subscription is selected for repository construction, so subscription policy discovery is not applicable. The learner preflight must check allowed locations, required tags, permitted resource types/SKUs, public-network restrictions, and role-assignment permissions before deployment.

---

## 3. Components

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| Support assistant | API and web application | Python 3.12, FastAPI, Microsoft Agent Framework | `src/support_assistant/` |
| Knowledge indexer | Setup utility | Python, Azure AI Search SDK | `scripts/seed_search.py` |
| Evaluation runner | Quality utility | Python, Microsoft Foundry evaluation APIs | `scripts/run_evaluation.py` |
| Learner curriculum | Documentation | Markdown | `labs/`, `docs/` |
| Infrastructure | IaC | Bicep, Azure Developer CLI | `infra/`, `azure.yaml` |

---

## 4. Recipe Selection

**Selected:** Azure Developer CLI with Bicep

**Rationale:**

- This is a new Azure-only, multi-service application.
- `azd` gives learners repeatable environment management, provisioning, packaging, deployment, and cleanup.
- Bicep provides inspectable first-party Azure IaC and supports modular resource definitions.
- The application is a single custom container, so Container Apps avoids Kubernetes overhead and supports scale to zero.

---

## 5. Architecture

**Stack:** One externally accessible Azure Container App hosts the FastAPI API and static chat UI. It calls a Microsoft Foundry project through Microsoft Agent Framework and retrieves synthetic support content from Azure AI Search. Application Insights and Log Analytics receive application and platform telemetry.

### Service mapping

| Component | Azure service | Configuration |
|-----------|---------------|---------------|
| Application image | Azure Container Registry | Basic SKU |
| API and web UI | Azure Container Apps | Consumption workload profile, 0-1 replicas, HTTPS-only ingress |
| AI project and Responses API | Microsoft Foundry account and project | Basic agent setup, project-scoped endpoint |
| Chat inference | Foundry model deployment | Configurable; support-oriented default documented, capacity checked before deployment |
| Vectorization | Foundry embeddings deployment | Configurable and capacity checked before deployment |
| Grounding | Azure AI Search | Free default for training, Basic override supported |
| Platform logs | Log Analytics | PerGB2018, short training retention |
| Application traces | Application Insights | Workspace-based |

### Runtime configuration

- Local development uses `DefaultAzureCredential`.
- Azure uses deterministic `ManagedIdentityCredential`.
- `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `EMBEDDING_MODEL`, `AZURE_AI_SEARCH_ENDPOINT`, `AZURE_AI_SEARCH_INDEX`, and Application Insights configuration are injected by `azd` outputs.
- A learner-generated bootcamp access token is stored as a Container Apps secret and is never committed.
- The container uses a non-root user, read-only application files, health probes, and explicit CPU/memory limits.

### Supporting services intentionally excluded

- No database: training conversations are bounded and in memory.
- No Storage account: synthetic documents are indexed from the repository.
- No Key Vault: Azure access is passwordless and the short-lived workshop token is a Container Apps secret. Production guidance recommends Entra authentication and Key Vault where application secrets exist.
- No private network: the cost-optimized workshop topology uses public service endpoints with Entra/RBAC. Production guidance documents private endpoints and network isolation.

---

## 6. Security

- Managed identity and Azure RBAC for Foundry, Search, monitoring, and registry access.
- No API keys, connection strings, tenant IDs, subscription IDs, or credentials in source control.
- Narrow resource-scope role assignments and explicit `principalType`.
- HTTPS-only ingress, conservative scaling, application rate limiting, request-size limits, and generated bootcamp-token protection.
- Synthetic content, citation preservation, indirect-prompt-injection tests, and no prompt/body logging by default.
- Pinned container base image line, pinned Python dependency ranges, and SHA-pinned GitHub Actions.
- OIDC for the optional GitHub deployment workflow; no client secrets.
- Learners must have `Microsoft.Authorization/roleAssignments/write` to provision required role assignments.

---

## 7. Provisioning Limit Checklist

No cloud deployment is authorized for repository construction. Actual usage and limits cannot be evaluated without the learner's subscription and region. Instead, `scripts/preflight.ps1` and `scripts/preflight.sh` will block `azd up` guidance until authentication, providers, policy, quota, and model capacity are checked.

| Resource type | Number to deploy | Repository-build usage | Learner deployment check |
|---------------|------------------|------------------------|--------------------------|
| `Microsoft.Resources/resourceGroups` | 1 | 0 | Confirm naming, tags, and location policy |
| `Microsoft.CognitiveServices/accounts` | 1 | 0 | Confirm account quota and region support |
| `Microsoft.CognitiveServices/accounts/projects` | 1 | 0 | Confirm Foundry provider availability |
| `Microsoft.CognitiveServices/accounts/deployments` | 2 | 0 | Confirm model/version/SKU capacity for chat and embeddings |
| `Microsoft.Search/searchServices` | 1 | 0 | Confirm Free SKU availability or select Basic |
| `Microsoft.ContainerRegistry/registries` | 1 | 0 | Confirm Basic registry quota |
| `Microsoft.App/managedEnvironments` | 1 | 0 | Confirm Container Apps environment quota |
| `Microsoft.App/containerApps` | 1 | 0 | Confirm app and managed environment quota |
| `Microsoft.OperationalInsights/workspaces` | 1 | 0 | Confirm workspace limit and retention policy |
| `Microsoft.Insights/components` | 1 | 0 | Confirm Application Insights availability |
| `Microsoft.Authorization/roleAssignments` | 5 | 0 | Confirm assignment permission and tenant policy |

**Status:** Deferred by approved no-provisioning scope; mandatory learner preflight is part of the generated repository.

---

## 8. Execution Checklist

### Planning

- [x] Analyze empty workspace as a new project
- [x] Gather learner, workload, scale, budget, and deployment requirements
- [x] Select Azure Developer CLI with Bicep
- [x] Research Microsoft Foundry, Container Apps, managed identity, observability, and secure CI guidance
- [x] Record the no-provisioning validation boundary
- [x] User approved the implementation plan

### Generation

- [ ] Initialize Git and public repository files
- [ ] Generate Python application, tests, local mock mode, and chat UI
- [ ] Generate container configuration
- [ ] Generate modular Bicep and `azure.yaml`
- [ ] Generate curriculum, scripts, and evaluation assets
- [ ] Generate CI and optional OIDC deployment workflow
- [ ] Apply security hardening
- [ ] Complete functional verification
- [ ] Set this plan to `Ready for Validation`

### Validation

- [ ] Invoke the `azure-validate` skill
- [ ] Validate Python formatting, linting, typing, and tests
- [ ] Validate Bicep and `azure.yaml`
- [ ] Build and smoke-test the production container
- [ ] Validate documentation links and secret hygiene
- [ ] Record proof below and set status to `Validated`

### Deployment

- [x] Deployment intentionally excluded from repository construction
- [ ] Learner invokes `azure-deploy` only after selecting Azure context and passing preflight

---

## 9. Validation Proof

| Check | Command | Result | Timestamp |
|-------|---------|--------|-----------|
| Pending | Pending generation | Pending | Pending |

**Validated by:** Pending `azure-validate` skill

---

## 10. Files to Generate

| File or directory | Purpose | Status |
|-------------------|---------|--------|
| `.azure/deployment-plan.md` | Deployment source of truth | Complete |
| `azure.yaml` | Azure Developer CLI project definition | Pending |
| `infra/` | Modular Bicep | Pending |
| `src/support_assistant/` | FastAPI, Agent Framework, retrieval, tools, and UI | Pending |
| `Dockerfile`, `.dockerignore` | Production container | Pending |
| `data/`, `scripts/` | Synthetic knowledge, evaluations, and automation | Pending |
| `labs/`, `docs/` | Self-paced curriculum and operations guides | Pending |
| `.github/workflows/` | CI and opt-in OIDC deployment | Pending |

---

## 11. Next Steps

> Current phase: generation

1. Create the repository foundation and Python application.
2. Generate and validate infrastructure and automation.
3. Complete functional verification.
4. Mark this plan `Ready for Validation` and invoke `azure-validate`.
