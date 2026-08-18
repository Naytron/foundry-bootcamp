"""Deployment retry classification tests."""

import pytest

from scripts.azd_deploy_with_retry import _is_transient_acr_failure


@pytest.mark.parametrize(
    "message",
    [
        "ImagePullBackOff: unauthorized while pulling crdemo.azurecr.io/app",
        "Failed to pull image from container registry: HTTP 403",
        "AcrPull role is still propagating: authentication required",
    ],
)
def test_identifies_transient_acr_authorization_failures(message: str) -> None:
    assert _is_transient_acr_failure(message)


@pytest.mark.parametrize(
    "message",
    [
        "HTTP 403 while creating a role assignment",
        "Container registry name is invalid",
        "Health probe failed with status 503",
    ],
)
def test_does_not_retry_unrelated_or_permanent_failures(message: str) -> None:
    assert not _is_transient_acr_failure(message)
