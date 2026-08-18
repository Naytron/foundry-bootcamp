# Cleanup

Cleanup is required after the cloud labs to stop ongoing charges.

## Review first

Before deleting anything:

1. Run `azd env get-values` and identify the environment and resource group.
2. Confirm the resource group contains only this workshop.
3. Save only evaluation or trace evidence you are permitted to retain.
4. Make sure no other learner depends on the environment.

## Delete the workshop environment

From the repository root:

```bash
azd down
```

Read the resources listed by `azd` and confirm only when the scope is correct. Deletion is destructive.

If organizational policy retains or soft-deletes a Foundry resource, follow the approved Azure administration process. Do not purge shared or unfamiliar resources.

## Verify

- The workshop resource group no longer exists.
- No Container App revision or Search service remains.
- Model deployments are gone.
- No scheduled workflow or deployment environment continues to target the deleted resources.

## Local cleanup

The following local paths are ignored by Git and can be removed when no longer needed:

- `.venv/`
- `.foundry/results/`
- `.azure/<environment-name>/`
- `.env`

Do not remove `.azure/deployment-plan.md`; it is versioned repository documentation.

