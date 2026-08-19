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
| Public clone and checkpoint tags | Pending | Updated after publication |
| Dev container setup | Pending | Updated after clean-room run |
| Day 1 local journey | Pending | Updated after clean-room run |
| Day 2 local journey | Pending | Updated after clean-room run |
| Day 3 local journey | Pending | Updated after clean-room run |
| Playwright UI journey | Pending | Updated after clean-room run |
| Deterministic evaluation | Pending | Expected baseline: 8/8 |
| Static quality and dependency audit | Pending | Updated after clean-room run |
| Bicep and production container | Pending | Updated after clean-room run |
| External documentation links | Pending | Updated after link check |
| Read-only Azure preflight/preview | Pending | No resources created |
| GitHub Actions CI | Pending | Updated after first public push |

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

