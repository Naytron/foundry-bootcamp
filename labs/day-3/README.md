# Day 3: Evaluate, Observe, Secure, and Deploy

Day 3 measures the capstone, adds privacy-conscious traces, reviews responsible-AI controls, and packages the application for Azure Container Apps.

**Track guidance:** Labs 3.1 and 3.3 have required local sections. Lab 3.2 and deployment/cleanup in Lab 3.4 are Azure extensions. Local-only learners complete the local validation section of Lab 3.4 and stop before deployment.

## Learning objectives

By the end of this day, you can:

- Turn expected behavior into a versioned evaluation dataset.
- Run deterministic quality gates against local or deployed endpoints.
- Submit prepared responses to Foundry cloud evaluators.
- Trace operations without recording message content by default.
- Apply the Discover, Protect, Govern responsible-AI lifecycle.
- Validate and deploy an `azd` and Bicep application.
- Verify and remove the deployed environment.

## Labs

1. [Evaluate the support agent](01-evaluate-the-agent.md)
2. [Trace and monitor the application](02-trace-and-monitor.md)
3. [Apply responsible AI and security controls](03-responsible-ai.md)
4. [Validate, deploy, and clean up](04-deploy-and-clean-up.md)

## Day checkpoint

You are complete when:

- The local evaluation reports 8/8 passing cases.
- Cloud evaluation remains explicitly opt-in.
- Message-content tracing is disabled in production.
- Bicep compiles and the production container builds.
- Local-only: Bicep, the production container, and local evaluation pass.
- Azure extension: the deployed app passes smoke/evaluation checks and the environment is deleted.

Stay on your learner branch. Use the [`day-3-complete` checkpoint](../../docs/checkpoints.md) only for comparison.
