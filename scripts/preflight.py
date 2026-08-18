"""Read-only preflight checks for a learner-selected Azure context."""

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Check:
    """One preflight result."""

    name: str
    status: str
    detail: str


def _run(command: list[str], *, timeout: int = 45) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(command[0])
    if not executable:
        return subprocess.CompletedProcess(command, 127, "", f"{command[0]} was not found")
    return subprocess.run(  # noqa: S603 - commands are fixed argument lists, never a shell string.
        [executable, *command[1:]],
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--location", default=os.getenv("AZURE_LOCATION"))
    parser.add_argument(
        "--chat-model",
        default=os.getenv("AZURE_AI_CHAT_MODEL_NAME", "gpt-4.1-mini"),
    )
    parser.add_argument(
        "--chat-version",
        default=os.getenv("AZURE_AI_CHAT_MODEL_VERSION", "2025-04-14"),
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("AZURE_AI_EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
    )
    parser.add_argument(
        "--embedding-version",
        default=os.getenv("AZURE_AI_EMBEDDING_MODEL_VERSION", "1"),
    )
    parser.add_argument(
        "--search-sku",
        default=os.getenv("AZURE_AI_SEARCH_SKU", "free"),
    )
    return parser.parse_args()


def _tool_checks() -> list[Check]:
    checks = []
    for tool in ("git", "python", "docker", "az", "azd"):
        path = shutil.which(tool)
        checks.append(
            Check(
                name=f"tool:{tool}",
                status="pass" if path else "fail",
                detail=path or "not found on PATH",
            )
        )
    return checks


def _provider_checks() -> list[Check]:
    providers = (
        "Microsoft.CognitiveServices",
        "Microsoft.Search",
        "Microsoft.ContainerRegistry",
        "Microsoft.App",
        "Microsoft.OperationalInsights",
        "Microsoft.Insights",
    )
    checks = []
    for provider in providers:
        result = _run(
            [
                "az",
                "provider",
                "show",
                "--namespace",
                provider,
                "--query",
                "registrationState",
                "--output",
                "tsv",
            ]
        )
        state = result.stdout.strip()
        checks.append(
            Check(
                name=f"provider:{provider}",
                status="pass" if result.returncode == 0 and state == "Registered" else "fail",
                detail=state
                or "provider lookup failed; register it through approved Azure governance",
            )
        )
    return checks


def _model_check(location: str, model: str, version: str, label: str) -> Check:
    result = _run(
        [
            "az",
            "cognitiveservices",
            "model",
            "list",
            "--location",
            location,
            "--output",
            "json",
        ]
    )
    if result.returncode != 0:
        return Check(
            name=f"model:{label}",
            status="fail",
            detail="model catalog lookup failed for the selected location",
        )
    models = json.loads(result.stdout)
    if not isinstance(models, list):
        return Check(
            name=f"model:{label}",
            status="fail",
            detail="model catalog returned an unexpected response",
        )
    available = False
    for item in models:
        definition = item.get("model") if isinstance(item.get("model"), dict) else item
        if definition.get("name") == model and str(definition.get("version")) == version:
            available = True
            break
    return Check(
        name=f"model:{label}",
        status="pass" if available else "fail",
        detail=f"{model} version {version} in {location}",
    )


def _search_check(search_sku: str) -> Check:
    if search_sku.casefold() != "free":
        return Check("search-sku", "pass", f"requested SKU: {search_sku}")
    result = _run(
        [
            "az",
            "resource",
            "list",
            "--resource-type",
            "Microsoft.Search/searchServices",
            "--query",
            "[?sku.name=='free'] | length(@)",
            "--output",
            "tsv",
        ]
    )
    if result.returncode != 0:
        return Check("search-sku", "warn", "could not determine existing Free services")
    count = int(result.stdout.strip() or "0")
    return Check(
        "search-sku",
        "pass" if count == 0 else "fail",
        "Free Search is available"
        if count == 0
        else "subscription already has a Free Search service",
    )


def _role_check(subscription_id: str) -> Check:
    principal = _run(["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"])
    if principal.returncode != 0 or not principal.stdout.strip():
        return Check(
            "role-assignment-permission",
            "warn",
            "could not resolve a signed-in user; verify roleAssignments/write manually",
        )
    assignments = _run(
        [
            "az",
            "role",
            "assignment",
            "list",
            "--assignee",
            principal.stdout.strip(),
            "--all",
            "--include-inherited",
            "--query",
            "[].{role:roleDefinitionName,scope:scope}",
            "--output",
            "json",
        ]
    )
    assignments_data = json.loads(assignments.stdout) if assignments.returncode == 0 else []
    allowed = {
        "Owner",
        "User Access Administrator",
        "Role Based Access Control Administrator",
    }
    subscription_scope = f"/subscriptions/{subscription_id}".casefold()
    matched = sorted(
        {
            item["role"]
            for item in assignments_data
            if item.get("role") in allowed
            and (
                str(item.get("scope", "")).casefold() == subscription_scope
                or str(item.get("scope", ""))
                .casefold()
                .startswith("/providers/microsoft.management/managementgroups/")
            )
        }
    )
    return Check(
        "role-assignment-permission",
        "pass" if matched else "warn",
        f"eligible role found: {', '.join(matched)}"
        if matched
        else "verify Microsoft.Authorization/roleAssignments/write at deployment scope",
    )


def _local_validation() -> list[Check]:
    checks = []
    docker = _run(["docker", "info", "--format", "{{.ServerVersion}}"])
    checks.append(
        Check(
            "docker-daemon",
            "pass" if docker.returncode == 0 else "fail",
            docker.stdout.strip() or "Docker daemon unavailable",
        )
    )
    bicep = _run(["az", "bicep", "build", "--file", "infra/main.bicep", "--stdout"])
    checks.append(
        Check(
            "bicep-build",
            "pass" if bicep.returncode == 0 else "fail",
            "infra/main.bicep compiles" if bicep.returncode == 0 else "Bicep compilation failed",
        )
    )
    return checks


def main() -> int:
    """Run checks without registering providers, assigning roles, or creating resources."""
    args = _arguments()
    checks = _tool_checks()
    if any(check.status == "fail" for check in checks):
        return _print_results(checks)

    account = _run(["az", "account", "show", "--output", "json"])
    if account.returncode != 0:
        checks.append(Check("azure-login", "fail", "run az login and select a subscription"))
        return _print_results(checks)
    account_data = json.loads(account.stdout)
    checks.append(
        Check(
            "azure-login",
            "pass",
            f"subscription selected: {account_data.get('name', 'unnamed')}",
        )
    )

    if not args.location:
        checks.append(
            Check(
                "azure-location",
                "fail",
                "set AZURE_LOCATION or pass --location after reviewing policy and capacity",
            )
        )
        return _print_results(checks)

    checks.extend(_provider_checks())
    checks.append(_model_check(args.location, args.chat_model, args.chat_version, "chat"))
    checks.append(
        _model_check(
            args.location,
            args.embedding_model,
            args.embedding_version,
            "embedding",
        )
    )
    checks.append(_search_check(args.search_sku))
    checks.append(_role_check(str(account_data["id"])))
    checks.extend(_local_validation())
    checks.append(
        Check(
            "model-quota",
            "warn",
            "confirm deployment SKU capacity and token quota in Foundry before azd up",
        )
    )
    return _print_results(checks)


def _print_results(checks: list[Check]) -> int:
    width = max(len(check.name) for check in checks)
    for check in checks:
        print(f"{check.status.upper():4}  {check.name:<{width}}  {check.detail}")
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
