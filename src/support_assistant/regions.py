"""Azure region defaults shared by setup and validation tools."""

DEFAULT_LOCATION = "eastus2"

SUGGESTED_LOCATIONS = (
    "eastus2",
    "swedencentral",
    "northcentralus",
    "eastus",
)

LOCATION_DISPLAY_NAMES = {
    "eastus2": "East US 2",
    "swedencentral": "Sweden Central",
    "northcentralus": "North Central US",
    "eastus": "East US",
}


def display_name(location: str) -> str:
    """Return a readable label for a suggested or custom Azure location."""
    return LOCATION_DISPLAY_NAMES.get(location, location)
