from unittest.mock import Mock

import pytest

from reevit.services.payouts import PayoutsService


def test_create_sends_idempotency_key_and_payload():
    client = Mock()
    client.request.return_value = {"id": "po_123"}
    service = PayoutsService(client)
    payload = {
        "connection_id": "conn_123",
        "amount": 2500,
        "currency": "GHS",
        "beneficiary_id": "ben_123",
    }

    assert service.create(payload, idempotency_key="order-123") == {"id": "po_123"}
    client.request.assert_called_once_with(
        "POST",
        "/v1/payouts",
        json=payload,
        headers={"Idempotency-Key": "order-123"},
    )


def test_create_rejects_blank_idempotency_key_without_request():
    client = Mock()
    service = PayoutsService(client)

    with pytest.raises(ValueError, match="idempotency_key is required"):
        service.create({}, idempotency_key="  ")

    client.request.assert_not_called()


def test_balance_uses_connection_query_parameter():
    client = Mock()
    client.request.return_value = {"balances": [{"currency": "GHS", "amount": 1000}]}
    service = PayoutsService(client)

    service.balance("conn_123")

    client.request.assert_called_once_with(
        "GET",
        "/v1/payouts/balance",
        params={"connection_id": "conn_123"},
    )
