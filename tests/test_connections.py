from unittest.mock import Mock

import pytest

from reevit.client import ReevitAPIError
from reevit.services.connections import ConnectionsService


def test_connection_test_accepts_backend_ok_response():
    client = Mock()
    client.request.return_value = {"ok": True}
    service = ConnectionsService(client)

    assert service.test({"provider": "paystack"}) is True


def test_list_all_follows_pagination_and_preserves_filters():
    client = Mock()
    client.request.side_effect = [
        {
            "connections": [{"id": "conn_1"}, {"id": "conn_2"}],
            "pagination": {"total": 3, "limit": 200, "offset": 0},
        },
        {
            "connections": [{"id": "conn_3"}],
            "pagination": {"total": 3, "limit": 200, "offset": 2},
        },
    ]
    service = ConnectionsService(client)

    connections = service.list_all(
        provider="paystack", mode="live", status="active", label="primary"
    )

    assert [connection["id"] for connection in connections] == [
        "conn_1",
        "conn_2",
        "conn_3",
    ]
    assert client.request.call_args_list[0].kwargs["params"] == {
        "provider": "paystack",
        "mode": "live",
        "status": "active",
        "label": "primary",
        "limit": 200,
        "offset": 0,
    }
    assert client.request.call_args_list[1].kwargs["params"]["offset"] == 2


def test_list_rejects_malformed_wrapped_response():
    client = Mock()
    client.request.return_value = {
        "pagination": {"total": 4, "limit": 50, "offset": 0}
    }
    service = ConnectionsService(client)

    # A malformed response must not look like an empty connection list.
    with pytest.raises(ReevitAPIError) as excinfo:
        service.list()

    assert excinfo.value.code == "unexpected_response_shape"


def test_list_rejects_a_non_object_response():
    client = Mock()
    client.request.return_value = "nope"
    service = ConnectionsService(client)

    with pytest.raises(ReevitAPIError) as excinfo:
        service.list()

    assert excinfo.value.code == "unexpected_response_shape"


def test_list_labels_uses_connection_labels_endpoint():
    client = Mock()
    client.request.return_value = [{"label": "primary", "total": 2}]
    service = ConnectionsService(client)

    assert service.list_labels() == [{"label": "primary", "total": 2}]
    client.request.assert_called_once_with("GET", "/v1/connections/labels")
