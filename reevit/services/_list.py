"""Shared helper for defensively unwrapping list responses.

The backend today returns list endpoints as either a bare array or a flat
``{"<key>": [...]}`` object. It may in future wrap responses in an envelope
(``{"data": [...], "pagination": {...}}``) or, for some endpoints, a
double-nested envelope (``{"data": {"<key>": [...]}, "pagination": {...}}``)
-- the shape already used in production by the admin audit-logs endpoint.

``extract_list`` resolves all of these shapes to a plain list, in an order
that is load-bearing: the legacy flat key is checked *before* ``data``, which
is what makes this a provable no-op against the server as it behaves today.
"""

from typing import Any, Dict, List


def extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    """Resolve ``payload`` to a list, tolerating several response shapes.

    Resolution order (do not reorder):
      1. ``payload`` is a list -> return it.
      2. ``payload`` is a dict:
         a. ``payload[key]`` is a list -> return it.
         b. ``payload["data"]`` is a list -> return it.
         c. ``payload["data"]`` is a dict and ``payload["data"][key]`` is a
            list -> return it.
      3. otherwise -> return ``[]``.

    Every candidate is type-checked with ``isinstance(..., list)`` before
    being returned, so a non-list value living at any of these keys is
    treated as a miss rather than returned as-is.
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        flat = payload.get(key)
        if isinstance(flat, list):
            return flat

        data = payload.get("data")
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            nested = data.get(key)
            if isinstance(nested, list):
                return nested

    return []
