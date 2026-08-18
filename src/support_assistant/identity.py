"""Environment-aware Azure credential creation."""

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from support_assistant.config import Settings

AzureCredential = DefaultAzureCredential | ManagedIdentityCredential


def create_credential(settings: Settings) -> AzureCredential:
    """Use developer credentials locally and deterministic managed identity in Azure."""
    if settings.app_env == "production":
        if settings.azure_client_id:
            return ManagedIdentityCredential(client_id=settings.azure_client_id)
        return ManagedIdentityCredential()

    return DefaultAzureCredential(exclude_interactive_browser_credential=False)
