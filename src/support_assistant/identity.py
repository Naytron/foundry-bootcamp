"""Environment-aware Azure credential creation."""

from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from support_assistant.config import Settings


def create_credential(settings: Settings) -> TokenCredential:
    """Use developer credentials locally and deterministic managed identity in Azure."""
    if settings.app_env == "production":
        if settings.azure_client_id:
            return ManagedIdentityCredential(client_id=settings.azure_client_id)
        return ManagedIdentityCredential()

    return DefaultAzureCredential(exclude_interactive_browser_credential=False)
