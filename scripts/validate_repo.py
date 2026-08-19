"""Validate repository structure, local links, data files, and secret hygiene."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "README.md",
    "LICENSE",
    ".devcontainer/devcontainer-lock.json",
    "azure.yaml",
    "infra/main.bicep",
    "pyproject.toml",
    "Dockerfile",
    "docs/checkpoints.md",
    "docs/e2e-validation.md",
    "docs/regions.md",
    "labs/day-1/README.md",
    "labs/day-2/README.md",
    "labs/day-3/README.md",
    "data/evaluations/support-agent.jsonl",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ACTION_REFERENCE = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Azure storage key": re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "real instrumentation key": re.compile(
        r"InstrumentationKey=[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    ),
}
IGNORED_DIRECTORIES = {
    ".git",
    ".foundry",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
LAB_HEADINGS = ("## Objective", "## Verify", "## Knowledge check")


def _tracked_text_files() -> list[Path]:
    suffixes = {
        ".bicep",
        ".css",
        ".html",
        ".js",
        ".json",
        ".jsonl",
        ".md",
        ".ps1",
        ".py",
        ".sh",
        ".toml",
        ".yaml",
        ".yml",
    }
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in suffixes
        and not IGNORED_DIRECTORIES & set(path.parts)
    ]


def _validate_required_paths() -> list[str]:
    return [
        f"missing required path: {path}" for path in REQUIRED_PATHS if not (ROOT / path).exists()
    ]


def _validate_markdown_links(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        if path.suffix.casefold() != ".md":
            continue
        for target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            clean_target = target.split("#", 1)[0].strip()
            if (
                not clean_target
                or "://" in clean_target
                or clean_target.startswith(("mailto:", "#"))
            ):
                continue
            resolved = (path.parent / clean_target).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    return errors


def _validate_structured_files(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        try:
            if path.suffix.casefold() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix.casefold() == ".jsonl":
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        json.loads(line)
            elif path.suffix.casefold() in {".yaml", ".yml"}:
                yaml.safe_load(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid structured data: {exc}")
    return errors


def _scan_secrets(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: possible {label}")
    return errors


def _validate_action_pins(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        if path.parent.name != "workflows" or path.suffix.casefold() not in {".yml", ".yaml"}:
            continue
        for action, reference in ACTION_REFERENCE.findall(path.read_text(encoding="utf-8")):
            if not action.startswith("./") and not COMMIT_SHA.fullmatch(reference):
                errors.append(
                    f"{path.relative_to(ROOT)}: action {action} must use a full commit SHA"
                )
    return errors


def _validate_curriculum() -> list[str]:
    errors = []
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    learner_phrases = (
        "git clone https://github.com/naytron/foundry-bootcamp.git",
        "Stay on `main`",
        "Choose a learning track",
        "docs/checkpoints.md",
        "docs/regions.md",
    )
    errors.extend(
        f"README.md: missing learner guidance: {phrase}"
        for phrase in learner_phrases
        if phrase not in root_readme
    )

    for day_dir in sorted((ROOT / "labs").glob("day-*")):
        day_readme = (day_dir / "README.md").read_text(encoding="utf-8")
        if "Track guidance:" not in day_readme:
            errors.append(f"{day_dir.relative_to(ROOT)}/README.md: missing track guidance")
        for lab in sorted(day_dir.glob("*.md")):
            if lab.name == "README.md":
                continue
            text = lab.read_text(encoding="utf-8")
            errors.extend(
                f"{lab.relative_to(ROOT)}: missing {heading}"
                for heading in LAB_HEADINGS
                if heading not in text
            )
            if f"]({lab.name})" not in day_readme:
                errors.append(f"{day_dir.relative_to(ROOT)}/README.md: does not link {lab.name}")

    combined_labs = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "labs").rglob("*.md")
    )
    obsolete_phrases = (
        "After Day 1 cloud setup",
        "Create a temporary local document that contains",
        "\npython scripts/run_evaluation.py --cloud\n",
    )
    errors.extend(
        f"labs: obsolete ambiguous guidance remains: {obsolete}"
        for obsolete in obsolete_phrases
        if obsolete in combined_labs
    )
    return errors


def main() -> int:
    files = _tracked_text_files()
    errors = [
        *_validate_required_paths(),
        *_validate_markdown_links(files),
        *_validate_structured_files(files),
        *_scan_secrets(files),
        *_validate_action_pins(files),
        *_validate_curriculum(),
    ]
    if errors:
        for error in errors:
            print(f"FAIL  {error}")
        return 1
    print(f"PASS  validated {len(files)} repository text files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
