"""Synthetic support-tool tests."""

from support_assistant.tools.support import create_case_draft, get_warranty_record


def test_known_warranty_record_is_returned() -> None:
    record = get_warranty_record("cts-10001")

    assert record["status"] == "active"
    assert record["coverage_end"] == "2027-03-14"


def test_unknown_warranty_record_has_safe_next_step() -> None:
    record = get_warranty_record("unknown")

    assert record["status"] == "not_found"
    assert "proof of purchase" in record["next_step"]


def test_case_draft_is_deterministic_and_never_submitted() -> None:
    first = create_case_draft(
        product="Trail Sensor",
        summary="Sensor remains offline after reconnect steps.",
        urgency="normal",
    )
    second = create_case_draft(
        product="Trail Sensor",
        summary="Sensor remains offline after reconnect steps.",
        urgency="normal",
    )

    assert first == second
    assert first["status"] == "draft"
    assert first["submitted"] is False
