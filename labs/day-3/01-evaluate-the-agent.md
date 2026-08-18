# Lab 3.1: Evaluate the Support Agent

## Objective

Turn quality expectations into repeatable checks before deployment.

## Inspect the dataset

Open `data/evaluations/support-agent.jsonl`. The eight cases cover:

- Grounded account and warranty answers
- Device troubleshooting
- Safety escalation
- Warranty lookup
- Case-draft boundaries
- Indirect prompt injection
- Honest handling of an unsupported question

Each row separates expected behavior, expected sources, required phrases, and forbidden claims.

## Run the local suite

Start the app in mock mode, then run:

```bash
python scripts/run_evaluation.py \
  --base-url http://localhost:8000 \
  --token "$BOOTCAMP_ACCESS_TOKEN"
```

PowerShell can use the same command on one line with `$env:BOOTCAMP_ACCESS_TOKEN`.

Review:

- `.foundry/results/local-evaluation.json`
- `.foundry/results/prepared-cloud-evaluation.jsonl`

The local checks are deterministic and suitable for CI. They do not replace model-based evaluation or human review.

## Optional cloud evaluation

Cloud evaluation is billable and requires a configured Foundry project:

```bash
python scripts/run_evaluation.py --cloud
```

The runner uploads the prepared response dataset and applies relevance, groundedness, task adherence, intent resolution, violence, and indirect-attack evaluators. Review the report URL printed by the script.

Read [cloud evaluation with the Foundry SDK](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation).

## Verify

- Local pass rate is 100%.
- A deliberately changed required phrase fails the quality gate.
- No access token is written to result files.
- Cloud runs are stored under `.foundry/results/`, which is ignored by Git.

## Knowledge check

1. Why should deterministic checks run before LLM-judge evaluation?
2. Why does the cloud dataset contain response context?
3. Which failures require a human reviewer rather than prompt tuning?

