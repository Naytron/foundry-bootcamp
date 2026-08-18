# Contributing

Contributions that improve correctness, accessibility, learner clarity, and cross-platform reliability are welcome.

## Development setup

1. Use the included dev container or Python 3.12.
2. Copy `.env.example` to `.env` and keep `USE_MOCK_SERVICES=true`.
3. Install the project with `python -m pip install -e ".[dev]"`.
4. Run `python -m pytest`, `ruff check .`, `ruff format --check .`, and `mypy src`.

## Content guidelines

- Keep labs self-paced and platform-neutral across Windows, macOS, Linux, and Codespaces.
- Give every exercise an objective, steps, verification, recovery guidance, and a knowledge check.
- Use synthetic data only.
- Link to current first-party Microsoft documentation for Azure behavior.
- Never include credentials, tenant data, subscription IDs, or screenshots containing personal information.
- Prefer clear language, meaningful link text, descriptive headings, and image alt text.

## Pull requests

Keep changes focused. Explain learner impact, list validation performed, and identify any Azure cost, permission, preview, or regional-availability implications.

