# Checkpoint Guide

The bootcamp curriculum lives on `main`. Stay on `main` or your learner branch while reading the labs.

The tags capture the implementation at the end of each build phase:

| Tag | Snapshot |
|-----|----------|
| `bootcamp-start` | Public repository foundation before application code |
| `day-1-complete` | Local API, web UI, Foundry adapter, and Day 1 tests |
| `day-2-complete` | Grounding, citations, synthetic knowledge, and tools |
| `day-3-complete` | Evaluations, observability, infrastructure, automation, and full curriculum |

Use tags without switching away from your learner branch:

```bash
git show day-1-complete:src/support_assistant/main.py
git diff day-1-complete..day-2-complete -- src tests
git diff day-2-complete..day-3-complete --stat
```

If you intentionally want a disposable snapshot branch:

```bash
git switch -c explore/day-2 day-2-complete
```

Return with `git switch learner/my-name`. Uncommitted changes can block switching, so commit or stash learner work first.
