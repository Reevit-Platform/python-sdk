"""Percent-encoding for URL path segments.

Every service interpolates ids into request paths. Without escaping, an id
containing ``/``, ``?`` or ``#`` silently rewrites the request: a customer id
of ``cust_1/../../admin`` walks the path, and ``cust_1?admin=1`` turns the rest
of the segment into a query string. Both are server-side authorisation
problems handed a free rewrite by the client.

``_seg`` percent-encodes the *whole* value -- ``safe=""`` means even ``/`` is
encoded -- so an id can only ever be one path segment.
"""

from typing import Any
from urllib.parse import quote


def seg(value: Any) -> str:
    """Percent-encode ``value`` for use as a single URL path segment.

    >>> seg("cust_1/../admin")
    'cust_1%2F..%2Fadmin'
    >>> seg("pay_ok")
    'pay_ok'
    """
    return quote(str(value), safe="")
