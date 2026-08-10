"""Tests for the shared defensive list-envelope helper.

Covers every response shape the SDK must tolerate:
  1. bare array (legacy)
  2. legacy flat key, e.g. {"customers": [...]}
  3. the new envelope, {"data": [...], "pagination": {...}}
  4. the double-nested shape already live at the admin audit-logs endpoint,
     {"data": {"logs": [...]}, "pagination": {...}}
plus the miss case, where none of the shapes match.

Also exercises the services that route through the helper to make sure the
wiring is a no-op against today's server response shapes (1 and 2).
"""

from unittest.mock import Mock

from reevit.services._list import extract_list
from reevit.services.connections import ConnectionsService
from reevit.services.customers import CustomersService
from reevit.services.payments import PaymentsService
from reevit.services.subscriptions import SubscriptionsService


# --- extract_list: shape coverage -----------------------------------------


def test_extract_list_bare_array():
    assert extract_list([{"id": "1"}, {"id": "2"}], "customers") == [
        {"id": "1"},
        {"id": "2"},
    ]


def test_extract_list_legacy_flat_key():
    payload = {"customers": [{"id": "1"}]}
    assert extract_list(payload, "customers") == [{"id": "1"}]


def test_extract_list_new_envelope():
    payload = {"data": [{"id": "1"}], "pagination": {"total": 1}}
    assert extract_list(payload, "customers") == [{"id": "1"}]


def test_extract_list_double_nested_envelope():
    payload = {"data": {"logs": [{"id": "1"}]}, "pagination": {"total": 1}}
    assert extract_list(payload, "logs") == [{"id": "1"}]


def test_extract_list_miss_returns_empty():
    assert extract_list({"unrelated": "value"}, "customers") == []
    assert extract_list(None, "customers") == []
    assert extract_list("not a payload", "customers") == []


def test_extract_list_flat_key_checked_before_data():
    # If both the legacy flat key and "data" are present, the flat key wins
    # (load-bearing order -- makes today's responses a provable no-op).
    payload = {"customers": [{"id": "flat"}], "data": [{"id": "enveloped"}]}
    assert extract_list(payload, "customers") == [{"id": "flat"}]


def test_extract_list_ignores_non_list_candidates():
    # A non-list value at the key (or at "data") must not be returned as-is.
    assert extract_list({"customers": {"not": "a list"}}, "customers") == []
    assert extract_list({"data": "not a list either"}, "customers") == []
    assert extract_list({"data": {"customers": "still not a list"}}, "customers") == []


# --- service wiring: provable no-op against today's server shapes ---------


def test_customers_list_unwraps_legacy_flat_key():
    client = Mock()
    client.request.return_value = {"customers": [{"id": "cust_1"}]}
    service = CustomersService(client)

    assert service.list() == [{"id": "cust_1"}]


def test_customers_list_unwraps_bare_array():
    client = Mock()
    client.request.return_value = [{"id": "cust_1"}]
    service = CustomersService(client)

    assert service.list() == [{"id": "cust_1"}]


def test_payments_list_unwraps_bare_array():
    client = Mock()
    client.request.return_value = [{"id": "pay_1"}]
    service = PaymentsService(client)

    assert service.list() == [{"id": "pay_1"}]


def test_payments_list_unwraps_new_envelope():
    client = Mock()
    client.request.return_value = {
        "data": [{"id": "pay_1"}],
        "pagination": {"total": 1},
    }
    service = PaymentsService(client)

    assert service.list() == [{"id": "pay_1"}]


def test_subscriptions_list_unwraps_bare_array():
    client = Mock()
    client.request.return_value = [{"id": "sub_1"}]
    service = SubscriptionsService(client)

    assert service.list() == [{"id": "sub_1"}]


def test_subscriptions_list_unwraps_legacy_flat_key():
    client = Mock()
    client.request.return_value = {"subscriptions": [{"id": "sub_1"}]}
    service = SubscriptionsService(client)

    assert service.list() == [{"id": "sub_1"}]


def test_connections_list_audit_unwraps_bare_array():
    client = Mock()
    client.request.return_value = [{"id": "audit_1"}]
    service = ConnectionsService(client)

    assert service.list_audit("conn_1") == [{"id": "audit_1"}]


def test_connections_list_audit_unwraps_legacy_flat_key():
    client = Mock()
    client.request.return_value = {"audit": [{"id": "audit_1"}]}
    service = ConnectionsService(client)

    assert service.list_audit("conn_1") == [{"id": "audit_1"}]


def test_connections_list_audit_unwraps_new_envelope():
    client = Mock()
    client.request.return_value = {
        "data": [{"id": "audit_1"}],
        "pagination": {"total": 1},
    }
    service = ConnectionsService(client)

    assert service.list_audit("conn_1") == [{"id": "audit_1"}]


def test_connections_list_page_still_unwraps_bare_array():
    client = Mock()
    client.request.return_value = [{"id": "conn_1"}]
    service = ConnectionsService(client)

    page = service.list_page()
    assert page["connections"] == [{"id": "conn_1"}]


def test_connections_list_page_still_rejects_malformed_response():
    client = Mock()
    client.request.return_value = {"pagination": {"total": 4}}
    service = ConnectionsService(client)

    try:
        service.list()
    except ValueError as error:
        assert "missing connections array" in str(error)
    else:
        raise AssertionError("malformed response should not look like an empty connection list")
