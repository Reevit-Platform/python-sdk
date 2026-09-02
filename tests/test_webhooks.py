"""Tests for Reevit webhook signature verification.

Imports the stdlib-only ``reevit.webhooks`` module directly so the suite does not
require ``requests`` (pulled in by ``reevit.client``).
"""

from datetime import datetime, timedelta, timezone

import pytest

from reevit.webhooks import (
    WebhookVerificationError,
    construct_event,
    sign_webhook_payload,
    verify_webhook_signature,
    verify_webhook_signature_with_tolerance,
)

# Canonical known-answer vector shared across the Node, Python and PHP SDK tests.
# The signature is HMAC-SHA256(secret, body) hex, prefixed with "sha256=", which
# is exactly what the Go backend emits in the X-Reevit-Signature header.
SECRET = "whsec_test_2x9aBcDeFgHiJkLmNoPqRsTuVwXyZ012"
BODY = (
    '{"event":"payment.updated","org_id":"org_123",'
    '"signature_timestamp":"2026-06-13T12:00:00Z",'
    '"data":{"id":"pay_abc","status":"succeeded"}}'
)
EXPECTED_SIG = "sha256=8fed6e24bd1c97ac5634ec88081a8299107706bf488290513bc3e5c5340e1950"


def test_sign_matches_known_vector():
    assert sign_webhook_payload(BODY, SECRET) == EXPECTED_SIG


def test_sign_accepts_bytes():
    assert sign_webhook_payload(BODY.encode("utf-8"), SECRET) == EXPECTED_SIG


def test_verify_accepts_valid_signature():
    assert verify_webhook_signature(BODY, EXPECTED_SIG, SECRET) is True


def test_verify_rejects_tampered_body():
    tampered = BODY.replace("succeeded", "failed")
    assert verify_webhook_signature(tampered, EXPECTED_SIG, SECRET) is False


def test_verify_rejects_wrong_secret():
    assert verify_webhook_signature(BODY, EXPECTED_SIG, "whsec_wrong") is False


def test_verify_rejects_missing_or_empty_inputs():
    assert verify_webhook_signature(BODY, None, SECRET) is False
    assert verify_webhook_signature(BODY, "", SECRET) is False
    assert verify_webhook_signature(BODY, EXPECTED_SIG, "") is False


def test_verify_rejects_signature_without_prefix():
    bare = EXPECTED_SIG.removeprefix("sha256=")
    assert verify_webhook_signature(BODY, bare, SECRET) is False


# --- replay tolerance -----------------------------------------------------

# The vector's body carries "signature_timestamp":"2026-06-13T12:00:00Z", so a
# reference "now" pinned to that instant makes the window checks deterministic.
SIGNED_AT = datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc)


def test_tolerance_accepts_a_fresh_delivery():
    assert (
        verify_webhook_signature_with_tolerance(
            BODY, EXPECTED_SIG, SECRET, now=SIGNED_AT + timedelta(seconds=30)
        )
        is True
    )


def test_tolerance_rejects_a_replayed_delivery():
    # Signature still valid -- only the age disqualifies it.
    assert verify_webhook_signature(BODY, EXPECTED_SIG, SECRET) is True
    assert (
        verify_webhook_signature_with_tolerance(
            BODY, EXPECTED_SIG, SECRET, now=SIGNED_AT + timedelta(seconds=301)
        )
        is False
    )


def test_tolerance_rejects_a_timestamp_too_far_in_the_future():
    assert (
        verify_webhook_signature_with_tolerance(
            BODY, EXPECTED_SIG, SECRET, now=SIGNED_AT - timedelta(seconds=301)
        )
        is False
    )


def test_tolerance_window_is_configurable():
    later = SIGNED_AT + timedelta(seconds=301)
    assert (
        verify_webhook_signature_with_tolerance(
            BODY, EXPECTED_SIG, SECRET, tolerance_seconds=3600, now=later
        )
        is True
    )


def test_tolerance_rejects_a_bad_signature_before_looking_at_the_clock():
    assert (
        verify_webhook_signature_with_tolerance(
            BODY, EXPECTED_SIG, "whsec_wrong", now=SIGNED_AT
        )
        is False
    )


def test_tolerance_rejects_a_body_without_a_signature_timestamp():
    body = '{"event":"payment.updated","org_id":"org_123"}'
    assert (
        verify_webhook_signature_with_tolerance(
            body, sign_webhook_payload(body, SECRET), SECRET, now=SIGNED_AT
        )
        is False
    )


# --- construct_event ------------------------------------------------------


def test_construct_event_returns_the_parsed_body():
    event = construct_event(
        BODY, EXPECTED_SIG, SECRET, now=SIGNED_AT + timedelta(seconds=5)
    )

    assert event["event"] == "payment.updated"
    assert event["data"] == {"id": "pay_abc", "status": "succeeded"}
    assert event["signature_timestamp"] == "2026-06-13T12:00:00Z"


def test_construct_event_accepts_bytes():
    event = construct_event(BODY.encode("utf-8"), EXPECTED_SIG, SECRET, now=SIGNED_AT)

    assert event["org_id"] == "org_123"


def test_construct_event_rejects_a_tampered_body():
    tampered = BODY.replace("succeeded", "failed")

    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(tampered, EXPECTED_SIG, SECRET, now=SIGNED_AT)

    assert excinfo.value.code == "invalid_signature"


def test_construct_event_rejects_a_missing_signature_header():
    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(BODY, None, SECRET, now=SIGNED_AT)

    assert excinfo.value.code == "invalid_signature"


def test_construct_event_rejects_a_replay():
    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(
            BODY, EXPECTED_SIG, SECRET, now=SIGNED_AT + timedelta(hours=1)
        )

    assert excinfo.value.code == "timestamp_out_of_tolerance"
    assert "tolerance" in str(excinfo.value)


def test_construct_event_rejects_a_body_without_a_timestamp():
    body = '{"event":"payment.updated"}'

    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(body, sign_webhook_payload(body, SECRET), SECRET)

    assert excinfo.value.code == "missing_signature_timestamp"


def test_construct_event_rejects_a_non_object_body():
    body = "[1, 2, 3]"

    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(body, sign_webhook_payload(body, SECRET), SECRET)

    assert excinfo.value.code == "invalid_payload"


def test_construct_event_rejects_a_non_json_body():
    body = "not json at all"

    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(body, sign_webhook_payload(body, SECRET), SECRET)

    assert excinfo.value.code == "invalid_payload"


def test_webhook_verification_error_is_a_value_error():
    # Existing `except ValueError` handlers around body parsing keep working.
    assert issubclass(WebhookVerificationError, ValueError)


@pytest.mark.parametrize(
    "stamp",
    [
        "2026-06-13T12:00:00Z",
        "2026-06-13T12:00:00.123456Z",
        "2026-06-13T12:00:00+00:00",
        "2026-06-13T13:00:00+01:00",
        "2026-06-13T11:00:00-01:00",
    ],
)
def test_construct_event_parses_rfc3339_variants(stamp):
    body = '{"event":"ping","signature_timestamp":"%s"}' % stamp

    event = construct_event(
        body, sign_webhook_payload(body, SECRET), SECRET, now=SIGNED_AT
    )

    assert event["event"] == "ping"


@pytest.mark.parametrize(
    "stamp",
    [
        "2026-06-13T12:00:00",  # RFC 3339 requires an offset
        "13/06/2026 12:00",
        "",
        "not a timestamp",
    ],
)
def test_construct_event_rejects_unparseable_timestamps(stamp):
    body = '{"event":"ping","signature_timestamp":"%s"}' % stamp

    with pytest.raises(WebhookVerificationError) as excinfo:
        construct_event(body, sign_webhook_payload(body, SECRET), SECRET, now=SIGNED_AT)

    assert excinfo.value.code == "missing_signature_timestamp"
