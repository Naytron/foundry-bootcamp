"""Run the support assistant with `python -m support_assistant`."""

import uvicorn

from support_assistant.config import get_settings


def main() -> None:
    """Start the FastAPI application."""
    settings = get_settings()
    uvicorn.run(
        "support_assistant.main:app",
        host=settings.app_host,
        port=settings.port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
