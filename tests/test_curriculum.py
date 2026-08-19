"""Learner curriculum contract tests."""

import pytest

from scripts.check_external_links import external_links
from scripts.preflight import _azd_environment_values, _with_subscription
from scripts.validate_repo import ROOT, _validate_curriculum


def test_curriculum_contract_is_complete() -> None:
    assert _validate_curriculum() == []


def test_checkpoint_guide_explains_all_tags() -> None:
    guide = (ROOT / "docs/checkpoints.md").read_text(encoding="utf-8")

    for tag in ("bootcamp-start", "day-1-complete", "day-2-complete", "day-3-complete"):
        assert f"`{tag}`" in guide
    assert "Stay on `main`" in guide


def test_external_link_inventory_is_nonempty_and_unique() -> None:
    links = external_links()

    assert links
    assert len(links) == len(set(links))
    assert all(link.startswith("https://") for link in links)


def test_preflight_adds_explicit_subscription() -> None:
    command = _with_subscription(["az", "account", "show"], "subscription-id")

    assert command[-2:] == ["--subscription", "subscription-id"]


def test_preflight_reads_selected_azd_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import preflight

    class Result:
        returncode = 0
        stdout = '{"AZURE_SUBSCRIPTION_ID":"sub","AZURE_LOCATION":"eastus2"}'

    monkeypatch.setattr(preflight, "_run", lambda command: Result())

    assert _azd_environment_values() == {
        "AZURE_SUBSCRIPTION_ID": "sub",
        "AZURE_LOCATION": "eastus2",
    }
