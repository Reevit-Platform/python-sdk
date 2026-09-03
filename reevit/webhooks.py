"""Webhook signature verification for Reevit outbound webhooks.

Reevit signs every outbound webhook with HMAC-SHA256 over the **raw request
body** and sends the result in the ``X-Reevit-Signature`` header as
``sha256=<hex>``. The signed body includes a ``signature_timestamp`` field, so
the signature also covers the timestamp (tamper protection). To additionally
guard against replay of a captured-but-recent delivery, check that
``signature_timestamp`` is recent after the signature verifies --
:func:`verify_webhook_signature_with_tolerance` and :func:`construct_event` do
that for you.

IMPORTANT: verify against the exact bytes you received. Do not ``json.loads``
and re-serialize the body first -- key order and whitespace must match what
Reevit signed, or the signature will not match.
"""

import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

_SIGNATURE_PREFIX = "sha256="

#: Field in the signed body carrying the RFC 3339 time Reevit signed at. This
#: name is set by the backend's outbound dispatcher and is identical across
#: every Reevit SDK -- changing it is a coordinated, all-languages release.
SIGNATURE_TIMESTAMP_FIELD = "signature_timestamp"

#: Default replay window, matching the other Reevit SDKs.
DEFAULT_TOLERANCE_SECONDS = 300


class WebhookVerificationError(ValueError):
    """Raised by :func:`construct_event` when a delivery cannot be trusted.

    Subclasses :class:`ValueError` so existing ``except ValueError`` handlers
    around body parsing keep working. Inspect :attr:`code` to tell the failure
    modes apart:

    ``invalid_signature``
        The HMAC did not match, or the signature header was missing.
    ``invalid_payload``
        The body was not a JSON object.
    ``missing_signature_timestamp``
        The signed body had no usable ``signature_timestamp``.
    ``timestamp_out_of_tolerance``
        The signature was valid but too old (or too far in the future) --
        a replay of a captured delivery.
    """

    def __init__(self, message: str, code: str):
        self.code = code
        super().__init__(message)


# RFC 3339 requires an explicit offset, so a naive timestamp is a miss rather
# than an assumed-UTC guess.
_RFC3339_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})[Tt ](?P<time>\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<frac>\d+))?"
    r"(?P<tz>[Zz]|[+-]\d{2}:?\d{2})$"
)


def _parse_rfc3339(value: Any) -> Optional[datetime]:
    """Parse an RFC 3339 timestamp into an aware datetime, or ``None``.

    Hand-rolled rather than ``datetime.fromisoformat`` because that only
    learned to accept a trailing ``Z`` in Python 3.11 and this package
    supports 3.9.
    """
    if not isinstance(value, str):
        return None

    match = _RFC3339_RE.match(value.strip())
    if match is None:
        return None

    tz_text = match.group("tz")
    if tz_text in ("Z", "z"):
        offset = timezone.utc
    else:
        digits = tz_text.replace(":", "")
        sign = -1 if digits[0] == "-" else 1
        offset = timezone(
            sign * timedelta(hours=int(digits[1:3]), minutes=int(digits[3:5]))
        )

    # Truncate to microsecond precision; Go emits nanoseconds in some formats.
    frac = (match.group("frac") or "")[:6].ljust(6, "0")
    parsed = datetime.strptime(
        f"{match.group('date')} {match.group('time')}", "%Y-%m-%d %H:%M:%S"
    )
    return parsed.replace(microsecond=int(frac), tzinfo=offset)


def _as_aware_utc(moment: Optional[datetime]) -> datetime:
    if moment is None:
        return datetime.now(timezone.utc)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


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


def verify_webhook_signature_with_tolerance(
    payload: Union[str, bytes],
    signature: Optional[str],
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[datetime] = None,
) -> bool:
    """Verify the signature *and* that the signed timestamp is recent.

    The signature already covers ``signature_timestamp``, so an attacker cannot
    forge the time -- but they can replay a delivery they captured verbatim.
    The tolerance window bounds how long such a replay stays useful.

    :param payload: Raw request body, exactly as received (str or bytes).
    :param signature: The ``X-Reevit-Signature`` header value (``sha256=...``).
    :param secret: The signing secret for the webhook endpoint.
    :param tolerance_seconds: Half-width of the accepted window, in seconds.
        Checked in both directions so a modest clock skew either way is
        tolerated rather than silently dropping live deliveries.
    :param now: Reference time (aware, or naive-as-UTC). Defaults to now.
    :returns: ``True`` only if the signature is valid, the body is a JSON
        object with a parseable ``signature_timestamp``, and that timestamp is
        within tolerance.
    """
    try:
        _verified_event(
            payload,
            signature,
            secret,
            tolerance_seconds=tolerance_seconds,
            now=now,
        )
    except WebhookVerificationError:
        return False
    return True


def construct_event(
    raw_body: Union[str, bytes],
    signature: Optional[str],
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Verify a delivery and return its parsed body in one step.

    The one call a webhook handler should make: it verifies the signature over
    the raw bytes, enforces the replay window, and only then parses -- so there
    is no way to accidentally act on an unverified body.

    :param raw_body: Raw request body, exactly as received. Do not
        ``json.loads`` and re-serialize first; key order and whitespace must
        match what Reevit signed.
    :returns: The decoded event object.
    :raises WebhookVerificationError: with ``.code`` set to one of
        ``invalid_signature``, ``invalid_payload``,
        ``missing_signature_timestamp`` or ``timestamp_out_of_tolerance``.
    """
    return _verified_event(
        raw_body,
        signature,
        secret,
        tolerance_seconds=tolerance_seconds,
        now=now,
    )


def _verified_event(
    payload: Union[str, bytes],
    signature: Optional[str],
    secret: str,
    *,
    tolerance_seconds: int,
    now: Optional[datetime],
) -> Dict[str, Any]:
    """Signature check, then window check, then parse. Order is load-bearing."""
    if not verify_webhook_signature(payload, signature, secret):
        raise WebhookVerificationError(
            "webhook signature verification failed", "invalid_signature"
        )

    try:
        event = json.loads(_to_bytes(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise WebhookVerificationError(
            f"webhook body is not valid JSON: {error}", "invalid_payload"
        ) from error

    if not isinstance(event, dict):
        raise WebhookVerificationError(
            f"webhook body is not a JSON object (got {type(event).__name__})",
            "invalid_payload",
        )

    signed_at = _parse_rfc3339(event.get(SIGNATURE_TIMESTAMP_FIELD))
    if signed_at is None:
        raise WebhookVerificationError(
            f"webhook body has no parseable {SIGNATURE_TIMESTAMP_FIELD} "
            "(expected an RFC 3339 timestamp)",
            "missing_signature_timestamp",
        )

    age = abs((_as_aware_utc(now) - signed_at).total_seconds())
    if age > tolerance_seconds:
        raise WebhookVerificationError(
            f"webhook {SIGNATURE_TIMESTAMP_FIELD} is {age:.0f}s away from now, "
            f"outside the {tolerance_seconds}s tolerance",
            "timestamp_out_of_tolerance",
        )

    return event
