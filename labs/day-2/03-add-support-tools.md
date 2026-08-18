# Lab 2.3: Add Deterministic Support Tools

## Objective

Use typed functions for operations that must be deterministic, constrained, and testable.

## Inspect the tools

Open `src/support_assistant/tools/support.py`.

The workshop exposes:

- `lookup_warranty` over two synthetic records.
- `draft_support_case`, which creates a deterministic draft and always returns `submitted: false`.

Try these synthetic serial numbers:

| Serial | Expected status |
|--------|-----------------|
| `CTS-10001` | Active |
| `CTS-20002` | Expired |
| `UNKNOWN` | Not found |

The tools have typed, bounded parameters. The agent instructions state that a draft is not a submitted case.

## Exercise

Ask:

```text
Look up warranty coverage for CTS-10001.
```

Then ask the assistant to draft a case for an offline Trail Sensor. Verify that it does not claim a case was submitted.

## Verify

```bash
python -m pytest tests/test_tools.py tests/test_foundry_provider.py
```

Review the tool result contract:

```json
{
  "status": "draft",
  "submitted": false
}
```

## Recovery

- No tool call: improve the tool description and parameter descriptions before adding prompt tricks.
- Invalid arguments: confirm the schema uses bounded string types and allowed urgency values.
- Agent claims submission: strengthen the system instruction and add an evaluation case; do not change the tool result to look successful.

## Knowledge check

1. Why is drafting safe to demonstrate while submission is omitted?
2. What information should never be accepted into a support-case tool?
3. When would a real tool need human approval, authorization, and idempotency?

## Stretch

Design a real submission boundary on paper. Include caller authorization, explicit confirmation, idempotency key, audit event, retry behavior, and a way to reconcile an unknown result.

