# Lab 3.3: Apply Responsible AI and Security Controls

## Objective

Review the capstone through the Microsoft Discover, Protect, Govern lifecycle.

Read [Responsible AI for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/responsible-use-of-ai-overview).

## Discover

Identify risks for:

- Incorrect support policy
- Unsafe device guidance
- Secret or personal-data disclosure
- Indirect prompt injection
- Unauthorized external action
- Citation laundering
- Cost abuse of a public endpoint

Map each risk to one or more evaluation cases.

## Protect

Review the implemented controls:

- Synthetic data and bounded inputs
- Project-level content filtering
- Untrusted retrieval delimiters
- Structured citations
- Typed tools with no submission capability
- Workshop bearer token and rate limit
- Managed identity and disabled local auth
- HTML-safe text rendering
- Message-content tracing disabled

Add one new adversarial case to the JSONL dataset and make the local suite pass.

Run the app and repeat the command from [Lab 3.1](01-evaluate-the-agent.md). Do not commit generated `.foundry/results/` files.

## Govern

Define:

- Quality and safety thresholds
- Human review ownership
- Trace retention
- Alert destinations
- Model or prompt change approval
- Incident response and rollback
- Data and citation review cadence

## Production gap review

The workshop intentionally omits Entra user sign-in, durable tenant-aware state, private endpoints, per-user Search filters, a real ticketing authorization layer, and multi-region resilience. Record which are required for your scenario before treating the sample as an architecture baseline.

## Verify

- Your new case has a unique ID and valid JSONL syntax.
- The deterministic suite passes all original cases plus your new case.
- The case tests observable behavior rather than hidden model reasoning.
- No secret, tenant data, or customer data is present.

## Knowledge check

1. Which control prevents tool execution from becoming unauthorized action?
2. Why is a correct citation not proof that the answer is correct?
3. How do preproduction evaluation and production monitoring complement each other?
