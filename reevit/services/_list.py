"""Shared helper for defensively unwrapping list responses.

The backend today returns list endpoints as either a bare array or a flat
``{"<key>": [...]}`` object. It may in future wrap responses in an envelope
(``{"data": [...], "pagination": {...}}``) or, for some endpoints, a
double-nested envelope (``{"data": {"<key>": [...]}, "pagination": {...}}``)
-- the shape already used in production by the admin audit-logs endpoint.

``extract_list`` resolves all of these shapes to a plain list, in an order
that is load-bearing: the legacy flat key is checked *before* ``data``, which
is what makes this a provable no-op against the server as it behaves today.

A shape it does *not* recognise raises ``ReevitAPIError`` rather than
returning ``[]``. An empty list is a real answer -- "this merchant has no
payments" -- and a reconciliation sweep that cannot tell it apart from "the
response shape changed" reports zero settlements instead of failing loudly.
Go and Rust already raise here; this brings Python in line.
"""

from typing import Any, Dict, List, NoReturn, Optional

_UNEXPECTED_SHAPE_CODE = "unexpected_response_shape"


def raise_unexpected_shape(payload: Any, key: str, message: Optional[str] = None) -> NoReturn:
    """Raise the SDK's canonical "I do not understand this body" error.

    Shared by ``extract_list`` and by services that resolve a list themselves,
    so every SDK surface reports the same ``unexpected_response_shape`` code.
    """
    # Imported lazily: reevit.client imports the services at module scope, so a
    # top-level import here would be circular.
    from reevit.client import ReevitAPIError

    raise ReevitAPIError(
        0,
        message
        or (
            f"unexpected response shape for {key!r}: could not find a list at "
            f"the top level, at {key!r}, at 'data', or at 'data.{key}' "
            f"(got {type(payload).__name__})"
        ),
        _UNEXPECTED_SHAPE_CODE,
        {"key": key, "received_type": type(payload).__name__},
    )


def extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    """Resolve ``payload`` to a list, tolerating several response shapes.

    Resolution order (do not reorder):
      1. ``payload`` is a list -> return it.
      2. ``payload`` is a dict:
         a. ``payload[key]`` is a list -> return it.
         b. ``payload["data"]`` is a list -> return it.
         c. ``payload["data"]`` is a dict and ``payload["data"][key]`` is a
            list -> return it.
      3. otherwise -> raise ``ReevitAPIError`` with code
         ``unexpected_response_shape``.

    Every candidate is type-checked with ``isinstance(..., list)`` before
    being returned, so a non-list value living at any of these keys is
    treated as a miss rather than returned as-is.

    A recognised container that happens to be empty (``[]``, ``{"<key>": []}``,
    ``{"data": []}``) still returns ``[]`` -- only an unrecognised shape raises.

    :raises ReevitAPIError: status ``0``, code ``unexpected_response_shape``.
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

    raise_unexpected_shape(payload, key)
