"""HTTP request and response models."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ChatRequest(BaseModel):
    """One user message sent to the support assistant."""

    message: Message
    session_id: UUID | None = None


class HealthResponse(BaseModel):
    """Health or readiness response."""

    status: str
    mode: str


class PublicConfigResponse(BaseModel):
    """Safe browser configuration that contains no credentials."""

    mode: str
    max_message_characters: int = Field(ge=1)
