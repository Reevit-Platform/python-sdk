"""Webhook signature verification for Reevit outbound webhooks.

Reevit signs every outbound webhook with HMAC-SHA256 over the **raw request
body** and sends the result in the ``X-Reevit-Signature`` header as
``sha256=<hex>``. The signed body includes a ``signature_timestamp`` field, so
the signature also covers the timestamp (tamper protection). To additionally
guard against replay of a captured-but-recent delivery, check that
``signature_timestamp`` is recent after the signature verifies.

IMPORTANT: verify against the exact bytes you received. Do not ``json.loads``
and re-serialize the body first -- key order and whitespace must match what
Reevit signed, or the signature will not match.
"""

import hashlib
import hmac
from typing import Optional, Union

_SIGNATURE_PREFIX = "sha256="


def _to_bytes(payload: Union[str, bytes]) -> bytes:
    return payload.encode("utf-8") if isinstance(payload, str) else payload


def sign_webhook_payload(payload: Union[str, bytes], secret: str) -> str:
    """Compute the ``X-Reevit-Signature`` header value for a raw webhook body.

    Returns ``sha256=<hex HMAC-SHA256 of the body>``. Primarily useful for tests.
    """
    digest = hmac.new(secret.encode("utf-8"), _to_bytes(payload), hashlib.sha256).hexdigest()
    return _SIGNATURE_PREFIX + digest


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature: Optional[str],
    secret: str,
) -> bool:
    """Verify a Reevit webhook signature in constant time.

    :param payload: Raw request body, exactly as received (str or bytes).
    :param signature: The ``X-Reevit-Signature`` header value (``sha256=...``).
    :param secret: The signing secret for the webhook endpoint.
    :returns: ``True`` only if the signature is present and valid.
    """
    if not signature or not secret:
        return False

    expected = sign_webhook_payload(payload, secret)

    # compare_digest is constant-time and length-safe.
    return hmac.compare_digest(expected, signature)
