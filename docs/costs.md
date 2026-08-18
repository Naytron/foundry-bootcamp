# Cost Guidance

Azure deployment is optional and billable. Prices, free grants, model availability, and regional capacity change; review the official calculators immediately before provisioning.

## Cost drivers

| Resource | Default workshop posture | Primary cost driver |
|----------|--------------------------|---------------------|
| Foundry model deployments | Low-capacity configurable deployments | Input/output and embeddings tokens |
| Azure AI Search | Free when available; Basic override | Provisioned Search service |
| Azure Container Apps | Consumption, zero minimum replicas, one maximum | Requests, CPU, and memory |
| Azure Container Registry | Basic | Stored images and data transfer |
| Application Insights and Log Analytics | Short retention | Telemetry ingestion and retention |
| Cloud evaluations | Small opt-in dataset | Judge-model and evaluation consumption |

## Before provisioning

1. Review [Azure pricing](https://azure.microsoft.com/pricing/).
2. Check [Foundry pricing](https://azure.microsoft.com/pricing/details/ai-foundry/).
3. Check [Azure AI Search pricing](https://azure.microsoft.com/pricing/details/search/).
4. Check [Container Apps pricing](https://azure.microsoft.com/pricing/details/container-apps/).
5. Confirm whether the subscription already uses its single Free Search service.
6. Confirm chat and embeddings quota in the selected region.
7. Set a budget or cost alert appropriate for the subscription.

## Cost controls in this repository

- No resource is created automatically.
- Search defaults to the Free SKU and can be overridden.
- Container Apps scales to zero and is capped at one replica.
- Model names, SKUs, and capacities are parameters.
- Evaluation uses eight synthetic cases.
- Telemetry content capture is off and retention is short.
- [Cleanup](cleanup.md) is part of Day 3, not an optional appendix.

Do not deploy the workshop into a production subscription without reviewing policy, networking, naming, tagging, and cost controls.

