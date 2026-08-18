# Day 3: Evaluate, Observe, Secure, and Deploy

Day 3 measures the capstone, adds privacy-conscious traces, reviews responsible-AI controls, and packages the application for Azure Container Apps.

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
- The deployed app passes health, chat, citation, and evaluation smoke checks.
- The Azure environment is deleted after use.

The `day-3-complete` Git tag records the reference checkpoint after repository generation.

