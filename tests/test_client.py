"""HTTP-level tests for the client transport.

These go through ``requests`` (via ``requests_mock``) rather than a ``Mock``
client, so they assert on the bytes actually put on the wire -- which is the
only way to prove that a path segment was escaped before it was sent.
"""

import pytest
import requests_mock

from reevit import Reevit, ReevitAPIError

API_KEY_TEST = "pfk_test_2x9aBcDeFgHiJkLmNoPqRsTuVwXyZ"
BASE_URL = "https://api.test.reevit.io"


def make_client(api_key: str = API_KEY_TEST) -> Reevit:
    return Reevit(api_key=api_key, org_id="org_123", base_url=BASE_URL)


# --- request id -----------------------------------------------------------


def test_api_error_captures_the_request_id_header():
    client = make_client()
    with requests_mock.Mocker() as http:
        http.get(
            f"{BASE_URL}/v1/payments/pay_123",
            status_code=404,
            json={"message": "payment not found", "code": "not_found"},
            headers={"X-Request-Id": "req_01HZY3"},
        )

        with pytest.raises(ReevitAPIError) as excinfo:
            client.payments.get("pay_123")

    error = excinfo.value
    assert error.request_id == "req_01HZY3"
    assert error.status_code == 404
    assert error.code == "not_found"


def test_api_error_str_includes_the_request_id():
    client = make_client()
    with requests_mock.Mocker() as http:
        http.get(
            f"{BASE_URL}/v1/payments/pay_123",
            status_code=500,
            json={"message": "internal error"},
            headers={"X-Request-Id": "req_abc"},
        )

        with pytest.raises(ReevitAPIError) as excinfo:
            client.payments.get("pay_123")

    assert str(excinfo.value) == "internal error (request_id=req_abc)"


def test_api_error_falls_back_to_the_legacy_request_id_header():
    client = make_client()
    with requests_mock.Mocker() as http:
        http.get(
            f"{BASE_URL}/v1/payments/pay_123",
            status_code=400,
            json={"message": "bad request"},
            headers={"X-Reevit-Request-Id": "req_legacy"},
        )

        with pytest.raises(ReevitAPIError) as excinfo:
            client.payments.get("pay_123")

    assert excinfo.value.request_id == "req_legacy"


def test_api_error_without_a_request_id_stringifies_unchanged():
    client = make_client()
    with requests_mock.Mocker() as http:
        http.get(
            f"{BASE_URL}/v1/payments/pay_123",
            status_code=400,
            json={"message": "bad request"},
        )

        with pytest.raises(ReevitAPIError) as excinfo:
            client.payments.get("pay_123")

    assert excinfo.value.request_id is None
    assert str(excinfo.value) == "bad request"
