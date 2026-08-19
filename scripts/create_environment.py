"""Create a local azd environment with a safe regional default and overrides."""

import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
from dataclasses import dataclass

from support_assistant.regions import (
    DEFAULT_LOCATION,
    SUGGESTED_LOCATIONS,
    display_name,
)

ENVIRONMENT_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
LOCATION_NAME = re.compile(r"^[a-z0-9]+$")


class EnvironmentSetupError(RuntimeError):
    """Raised when local azd environment setup cannot complete safely."""


@dataclass(frozen=True, slots=True)
class EnvironmentOptions:
    """Resolved values used to configure one local azd environment."""

    name: str
    subscription: str
    location: str
    principal_id: str
    principal_type: str


@dataclass(frozen=True, slots=True)
class SubscriptionContext:
    """Resolved Azure subscription and tenant identifiers."""

    subscription_id: str
    tenant_id: str


@dataclass(frozen=True, slots=True)
class EnvironmentInventory:
    """Local azd environment names and the currently selected environment."""

    names: frozenset[str]
    selected: str | None


def _arguments() -> argparse.Namespace:
    suggested = ", ".join(SUGGESTED_LOCATIONS)
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=f"Suggested locations: {suggested}",
    )
    parser.add_argument(
        "environment",
        nargs="?",
        help="Unique azd environment name; generated when omitted.",
    )
    parser.add_argument(
        "--subscription",
        help="Azure subscription ID or name; defaults to the current Azure CLI subscription.",
    )
    parser.add_argument(
        "--location",
        default=DEFAULT_LOCATION,
        help=f"Azure region (default: {DEFAULT_LOCATION}).",
    )
    parser.add_argument(
        "--principal-id",
        help="Object ID receiving learner roles; defaults to the signed-in user.",
    )
    parser.add_argument(
        "--principal-type",
        choices=("User", "Group", "ServicePrincipal"),
        default="User",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the resolved setup without creating local environment state.",
    )
    return parser.parse_args()


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise EnvironmentSetupError(f"Required command was not found on PATH: {name}")
    return path


def _run(command: list[str], *, sensitive: bool = False) -> subprocess.CompletedProcess[str]:
    executable = _tool(command[0])
    try:
        result = subprocess.run(  # noqa: S603 - executable is resolved and no shell is used.
            [executable, *command[1:]],
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        detail = "sensitive command timed out" if sensitive else f"{command[0]} timed out"
        raise EnvironmentSetupError(detail) from exc
    except OSError as exc:
        detail = "sensitive command failed" if sensitive else f"{command[0]} failed: {exc}"
        raise EnvironmentSetupError(detail) from exc
    if result.returncode:
        detail = "sensitive command failed" if sensitive else result.stderr.strip()
        raise EnvironmentSetupError(detail or f"{command[0]} exited with {result.returncode}")
    return result


def _default_environment_name() -> str:
    return f"foundry-bootcamp-{secrets.token_hex(4)}"


def _validate_environment_name(name: str) -> str:
    normalized = name.casefold()
    if not ENVIRONMENT_NAME.fullmatch(normalized):
        raise EnvironmentSetupError(
            "Environment names must be 1-64 lowercase letters, numbers, or hyphens; "
            "they must start and end with a letter or number."
        )
    return normalized


def _subscription_context(subscription: str | None = None) -> SubscriptionContext:
    command = ["az", "account", "show"]
    if subscription:
        command.extend(["--subscription", subscription])
    result = _run([*command, "--output", "json"])
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EnvironmentSetupError("Azure CLI returned invalid subscription data.") from exc
    if not isinstance(value, dict) or not value.get("id") or not value.get("tenantId"):
        raise EnvironmentSetupError("Azure CLI returned unexpected subscription data.")
    return SubscriptionContext(
        subscription_id=str(value["id"]),
        tenant_id=str(value["tenantId"]),
    )


def _signed_in_user() -> str:
    return _run(
        ["az", "ad", "signed-in-user", "show", "--query", "id", "--output", "tsv"]
    ).stdout.strip()


def _available_locations(subscription: str) -> set[str]:
    result = _run(
        [
            "az",
            "rest",
            "--method",
            "get",
            "--url",
            (
                "https://management.azure.com/subscriptions/"
                f"{subscription}/locations?api-version=2022-12-01"
            ),
            "--output",
            "json",
        ]
    )
    try:
        values = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EnvironmentSetupError("Azure CLI returned invalid location data.") from exc
    if not isinstance(values, dict) or not isinstance(values.get("value"), list):
        raise EnvironmentSetupError("Azure CLI returned unexpected location data.")
    return {
        str(item["name"]).casefold()
        for item in values["value"]
        if isinstance(item, dict) and item.get("name")
    }


def _environment_inventory() -> EnvironmentInventory:
    result = _run(["azd", "env", "list", "--output", "json"])
    try:
        values = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EnvironmentSetupError("azd returned invalid environment data.") from exc
    if not isinstance(values, list):
        raise EnvironmentSetupError("azd returned unexpected environment data.")
    names: set[str] = set()
    selected = None
    for item in values:
        if isinstance(item, str):
            names.add(item.casefold())
        elif isinstance(item, dict):
            value = item.get("name") or item.get("Name")
            if value:
                exact_name = str(value)
                normalized = exact_name.casefold()
                names.add(normalized)
                if item.get("isDefault") is True or item.get("IsDefault") is True:
                    selected = exact_name
    return EnvironmentInventory(frozenset(names), selected)


def _resolve_options(args: argparse.Namespace) -> EnvironmentOptions:
    name = _validate_environment_name(args.environment or _default_environment_name())
    requested_subscription = args.subscription.strip() if args.subscription is not None else None
    if requested_subscription == "":
        raise EnvironmentSetupError("No Azure subscription was provided or selected in Azure CLI.")
    if args.dry_run and requested_subscription:
        subscription = requested_subscription
    else:
        active_context = _subscription_context()
        target_context = (
            _subscription_context(requested_subscription)
            if requested_subscription
            else active_context
        )
        if not args.dry_run and target_context.tenant_id != active_context.tenant_id:
            raise EnvironmentSetupError(
                "The requested subscription is in a different tenant than the active Azure CLI "
                f"context. Run 'az login --tenant {target_context.tenant_id}' and select "
                f"subscription '{target_context.subscription_id}', then retry."
            )
        subscription = target_context.subscription_id
    location = args.location.strip().casefold()
    if not LOCATION_NAME.fullmatch(location):
        raise EnvironmentSetupError(
            "Azure locations must contain only lowercase letters and numbers, such as eastus2."
        )

    if args.principal_id:
        principal_id = args.principal_id.strip()
    elif args.principal_type == "User":
        principal_id = _signed_in_user().strip()
    else:
        raise EnvironmentSetupError(
            "--principal-id is required for Group or ServicePrincipal principals."
        )
    if not principal_id:
        raise EnvironmentSetupError("The learner principal ID could not be resolved.")

    if not args.dry_run and location not in _available_locations(subscription):
        raise EnvironmentSetupError(
            f"Azure location '{location}' is not available to subscription '{subscription}'."
        )

    return EnvironmentOptions(
        name=name,
        subscription=subscription,
        location=location,
        principal_id=principal_id,
        principal_type=args.principal_type,
    )


def _print_plan(options: EnvironmentOptions, *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "CREATED"
    qualifier = "default" if options.location == DEFAULT_LOCATION else "override"
    print(f"{mode}: local azd environment '{options.name}'")
    print(f"Subscription: {options.subscription}")
    print(f"Location: {display_name(options.location)} ({options.location}, {qualifier})")
    if options.location not in SUGGESTED_LOCATIONS:
        print(
            "Warning: this is outside the bootcamp's suggested regions; "
            "run preflight and provisioning preview, then manually confirm regional service "
            "support, policy, and quota."
        )
    if dry_run:
        print("No local environment or bootcamp access token was created.")


def _create_environment(options: EnvironmentOptions) -> None:
    inventory = _environment_inventory()
    if options.name in inventory.names:
        raise EnvironmentSetupError(f"azd environment already exists: {options.name}")

    created = False
    try:
        _run(
            [
                "azd",
                "env",
                "new",
                options.name,
                "--subscription",
                options.subscription,
                "--location",
                options.location,
                "--no-prompt",
            ]
        )
        created = True
        _run(
            [
                "azd",
                "env",
                "set",
                "--environment",
                options.name,
                "AZURE_PRINCIPAL_ID",
                options.principal_id,
            ]
        )
        _run(
            [
                "azd",
                "env",
                "set",
                "--environment",
                options.name,
                "AZURE_PRINCIPAL_TYPE",
                options.principal_type,
            ]
        )
        _run(
            [
                "azd",
                "env",
                "set",
                "--environment",
                options.name,
                "BOOTCAMP_ACCESS_TOKEN",
                secrets.token_urlsafe(32),
            ],
            sensitive=True,
        )
    except EnvironmentSetupError as exc:
        cleanup_errors = []
        if created:
            try:
                _run(["azd", "env", "remove", options.name, "--force"])
            except EnvironmentSetupError as cleanup_error:
                cleanup_errors.append(f"remove new environment: {cleanup_error}")
            if inventory.selected:
                try:
                    _run(["azd", "env", "select", inventory.selected, "--no-prompt"])
                except EnvironmentSetupError as cleanup_error:
                    cleanup_errors.append(
                        f"restore selected environment '{inventory.selected}': {cleanup_error}"
                    )
        if cleanup_errors:
            raise EnvironmentSetupError(
                f"{exc}; local environment cleanup also failed: {'; '.join(cleanup_errors)}"
            ) from exc
        raise


def main() -> int:
    try:
        args = _arguments()
        options = _resolve_options(args)
        if args.dry_run:
            _print_plan(options, dry_run=True)
            return 0

        _create_environment(options)
        _print_plan(options, dry_run=False)
        print("\nNext:")
        print("  python scripts/preflight.py")
        print("  azd provision --preview --no-prompt")
        return 0
    except EnvironmentSetupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
