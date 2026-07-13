"""Tests for Reevit webhook signature verification.

Imports the stdlib-only ``reevit.webhooks`` module directly so the suite does not
require ``requests`` (pulled in by ``reevit.client``).
"""

from reevit.webhooks import sign_webhook_payload, verify_webhook_signature

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
