"""Azure region and local azd environment tests."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import create_environment
from scripts.preflight import _location_sync_check, _resolve_location
from scripts.validate_repo import ROOT
from support_assistant.regions import DEFAULT_LOCATION, SUGGESTED_LOCATIONS, display_name

ACCOUNT_CONTEXT = '{"id":"sub","tenantId":"tenant"}'


def _set_arguments(monkeypatch: pytest.MonkeyPatch, *arguments: str) -> None:
    monkeypatch.setattr(sys, "argv", ["create_environment.py", *arguments])


def test_region_catalog_has_east_us_2_default() -> None:
    assert DEFAULT_LOCATION == "eastus2"
    assert SUGGESTED_LOCATIONS == (
        "eastus2",
        "swedencentral",
        "northcentralus",
        "eastus",
    )
    assert display_name(DEFAULT_LOCATION) == "East US 2"


def test_generated_environment_name_is_unique_shaped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(create_environment.secrets, "token_hex", lambda _: "a1b2c3d4")

    name = create_environment._default_environment_name()

    assert name == "foundry-bootcamp-a1b2c3d4"


def test_argument_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_arguments(monkeypatch, "--subscription", "sub")
    assert create_environment._arguments().location == "eastus2"

    _set_arguments(
        monkeypatch,
        "--subscription",
        "sub",
        "--location",
        "swedencentral",
    )
    assert create_environment._arguments().location == "swedencentral"


def test_dry_run_uses_default_without_disclosing_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_called(
        command: list[str],
        *,
        sensitive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        pytest.fail(f"dry-run invoked a command: {command}")

    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--principal-id",
        "principal",
        "--dry-run",
    )
    monkeypatch.setattr(create_environment, "_run", fail_if_called)

    assert create_environment.main() == 0
    output = capsys.readouterr()

    assert "East US 2 (eastus2, default)" in output.out
    assert "No local environment or bootcamp access token was created." in output.out


def test_environment_creation_uses_native_azd_region_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        sensitive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:3] == ["az", "account", "show"]:
            stdout = ACCOUNT_CONTEXT
        elif command[:2] == ["az", "rest"]:
            stdout = '{"value":[{"name":"swedencentral"}]}'
        elif command[:3] == ["azd", "env", "list"]:
            stdout = "[]"
        else:
            stdout = ""
        return subprocess.CompletedProcess(command, 0, stdout, "")

    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--location",
        "swedencentral",
        "--principal-id",
        "principal",
    )
    monkeypatch.setattr(create_environment, "_run", fake_run)
    monkeypatch.setattr(
        create_environment.secrets,
        "token_urlsafe",
        lambda _: "do-not-print-this-token",
    )

    assert create_environment.main() == 0
    output = capsys.readouterr()

    assert [
        "azd",
        "env",
        "new",
        "region-test",
        "--subscription",
        "sub",
        "--location",
        "swedencentral",
        "--no-prompt",
    ] in calls
    assert [
        "azd",
        "env",
        "set",
        "--environment",
        "region-test",
        "BOOTCAMP_ACCESS_TOKEN",
        "do-not-print-this-token",
    ] in calls
    assert "do-not-print-this-token" not in output.out + output.err


def test_duplicate_environment_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        sensitive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:3] == ["az", "account", "show"]:
            stdout = ACCOUNT_CONTEXT
        elif command[:2] == ["az", "rest"]:
            stdout = '{"value":[{"name":"eastus2"}]}'
        else:
            stdout = '[{"Name": "region-test"}]'
        return subprocess.CompletedProcess(command, 0, stdout, "")

    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--principal-id",
        "principal",
    )
    monkeypatch.setattr(create_environment, "_run", fake_run)

    assert create_environment.main() == 1
    output = capsys.readouterr()

    assert "already exists" in output.err
    assert not any(command[:3] == ["azd", "env", "new"] for command in calls)


def test_custom_region_warns_but_remains_overrideable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--location",
        "westus3",
        "--principal-id",
        "principal",
        "--dry-run",
    )
    monkeypatch.setattr(
        create_environment,
        "_run",
        lambda command, sensitive=False: subprocess.CompletedProcess(command, 0, "", ""),
    )

    assert create_environment.main() == 0
    output = capsys.readouterr()

    assert "westus3 (westus3, override)" in output.out
    assert "outside the bootcamp's suggested regions" in output.out


def test_configuration_failure_removes_only_new_local_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        sensitive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:3] == ["az", "account", "show"]:
            return subprocess.CompletedProcess(command, 0, ACCOUNT_CONTEXT, "")
        if command[:2] == ["az", "rest"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"value":[{"name":"eastus2"}]}',
                "",
            )
        if command[:3] == ["azd", "env", "list"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '[{"Name":"PriorEnv","IsDefault":true}]',
                "",
            )
        if "AZURE_PRINCIPAL_ID" in command:
            raise create_environment.EnvironmentSetupError("configuration failed")
        return subprocess.CompletedProcess(command, 0, "", "")

    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--principal-id",
        "principal",
    )
    monkeypatch.setattr(create_environment, "_run", fake_run)

    assert create_environment.main() == 1
    output = capsys.readouterr()

    assert "configuration failed" in output.err
    assert ["azd", "env", "remove", "region-test", "--force"] in calls
    assert ["azd", "env", "select", "PriorEnv", "--no-prompt"] in calls


def test_cross_tenant_subscription_requires_matching_cli_context(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(
        command: list[str],
        *,
        sensitive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        tenant = "other-tenant" if "--subscription" in command else "active-tenant"
        value = json.dumps({"id": "sub", "tenantId": tenant})
        return subprocess.CompletedProcess(command, 0, value, "")

    _set_arguments(
        monkeypatch,
        "region-test",
        "--subscription",
        "sub",
        "--principal-id",
        "principal",
    )
    monkeypatch.setattr(create_environment, "_run", fake_run)

    assert create_environment.main() == 1
    output = capsys.readouterr()

    assert "different tenant" in output.err
    assert "az login --tenant other-tenant" in output.err


def test_preflight_location_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_LOCATION", raising=False)
    assert _resolve_location(None, {}) == ("eastus2", "bootcamp default")
    assert _resolve_location(None, {"AZURE_LOCATION": "EastUS"}) == (
        "eastus",
        "selected azd environment",
    )

    monkeypatch.setenv("AZURE_LOCATION", "NorthCentralUS")
    assert _resolve_location(None, {"AZURE_LOCATION": "eastus"}) == (
        "northcentralus",
        "environment override",
    )
    assert _resolve_location("SwedenCentral", {"AZURE_LOCATION": "eastus"}) == (
        "swedencentral",
        "command-line override",
    )


def test_preflight_rejects_location_that_differs_from_selected_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AZURE_LOCATION", raising=False)
    matching = _location_sync_check("eastus2", {"AZURE_LOCATION": "EastUS2"})
    conflicting = _location_sync_check("swedencentral", {"AZURE_LOCATION": "eastus2"})
    missing_override = _location_sync_check("swedencentral", {})
    missing_default = _location_sync_check("eastus2", {})

    assert matching.status == "pass"
    assert conflicting.status == "fail"
    assert missing_override.status == "fail"
    assert missing_default.status == "pass"
    assert "azd env set AZURE_LOCATION swedencentral" in conflicting.detail

    monkeypatch.setenv("AZURE_LOCATION", "swedencentral")
    process_matching = _location_sync_check("swedencentral", {})
    process_conflicting = _location_sync_check("eastus2", {})

    assert process_matching.status == "pass"
    assert process_conflicting.status == "fail"


def test_all_deployment_surfaces_agree_on_default_region() -> None:
    parameters = json.loads((ROOT / "infra/main.parameters.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    region_guide = (ROOT / "docs/regions.md").read_text(encoding="utf-8")
    deployment_plan = (ROOT / ".azure/deployment-plan.md").read_text(encoding="utf-8")

    assert parameters["parameters"]["location"]["value"] == "${AZURE_LOCATION=eastus2}"
    assert re.search(r"location:\s*\n(?:.*\n){0,4}\s+default: eastus2", workflow)
    assert "Environment '$AZURE_ENV_NAME' already uses" in workflow
    assert '--tag "azd-env-name=$AZURE_ENV_NAME"' in workflow
    assert "Environment names must be 1-64 lowercase" in workflow
    assert "`eastus2`" in region_guide
    assert "East US 2 (`eastus2`) by default" in deployment_plan


@pytest.mark.parametrize(
    "path",
    [
        Path("README.md"),
        Path("docs/setup.md"),
        Path("labs/day-3/04-deploy-and-clean-up.md"),
    ],
)
def test_primary_docs_link_region_guide(path: Path) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")

    assert "regions.md" in text
