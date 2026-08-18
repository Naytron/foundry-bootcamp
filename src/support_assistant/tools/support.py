"""Synthetic support tools with no external side effects."""

import hashlib
import json
from typing import Annotated, Literal

from agent_framework import tool
from pydantic import Field

Urgency = Literal["low", "normal", "high", "urgent"]

_WARRANTY_RECORDS = {
    "CTS-10001": {
        "product": "Contoso Trail Sensor",
        "purchase_date": "2025-03-14",
        "coverage_end": "2027-03-14",
        "status": "active",
    },
    "CTS-20002": {
        "product": "Contoso Trail Gateway",
        "purchase_date": "2023-11-02",
        "coverage_end": "2025-11-02",
        "status": "expired",
    },
}


def get_warranty_record(serial_number: str) -> dict[str, str]:
    """Return one synthetic warranty record without exposing a real system."""
    normalized = serial_number.strip().upper()
    record = _WARRANTY_RECORDS.get(normalized)
    if record is None:
        return {
            "serial_number": normalized,
            "status": "not_found",
            "next_step": "Ask the customer for proof of purchase and draft a support case.",
        }
    return {"serial_number": normalized, **record}


def create_case_draft(*, product: str, summary: str, urgency: Urgency) -> dict[str, str | bool]:
    """Create a deterministic draft that a person must review outside this sample."""
    digest = hashlib.sha256(f"{product}|{summary}|{urgency}".encode()).hexdigest()[:8].upper()
    return {
        "draft_id": f"DRAFT-{digest}",
        "product": product.strip(),
        "summary": summary.strip(),
        "urgency": urgency,
        "status": "draft",
        "submitted": False,
        "next_step": (
            "Review the draft and explicitly confirm it in an authorized ticketing system."
        ),
    }


@tool(approval_mode="never_require")
def lookup_warranty(
    serial_number: Annotated[
        str,
        Field(
            min_length=3,
            max_length=40,
            description="Synthetic device serial number, for example CTS-10001.",
        ),
    ],
) -> str:
    """Look up a synthetic Contoso warranty record."""
    return json.dumps(get_warranty_record(serial_number), separators=(",", ":"))


@tool(approval_mode="never_require")
def draft_support_case(
    product: Annotated[str, Field(min_length=2, max_length=100)],
    summary: Annotated[str, Field(min_length=10, max_length=1_000)],
    urgency: Urgency = "normal",
) -> str:
    """Draft, but never submit, a synthetic support case."""
    return json.dumps(
        create_case_draft(product=product, summary=summary, urgency=urgency),
        separators=(",", ":"),
    )


SUPPORT_TOOLS = [lookup_warranty, draft_support_case]
