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


# --- path segment escaping ------------------------------------------------

# ``request_history[…].path`` is lower-cased by requests_mock; ``path_url``
# preserves the bytes actually sent, which is what these tests are about.


def test_an_id_containing_a_slash_cannot_escape_its_path_segment():
    """A `/` in an id must be percent-encoded, not treated as a separator.

    Unescaped, `pay_1/../../v1/admin` resolves server-side to a completely
    different endpoint than the one the caller asked for.
    """
    client = make_client()

    with requests_mock.Mocker() as http:
        http.get(requests_mock.ANY, json={"id": "pay_1"})

        assert client.payments.get("pay_1/../../v1/admin") == {"id": "pay_1"}
        sent = http.request_history[0]

    # One segment on the wire, not four.
    assert sent.path_url == "/v1/payments/pay_1%2F..%2F..%2Fv1%2Fadmin"
    assert "/v1/admin" not in sent.path_url


def test_an_id_containing_a_question_mark_does_not_become_a_query_string():
    client = make_client()

    with requests_mock.Mocker() as http:
        http.get(requests_mock.ANY, json={"id": "cust_1"})

        client.customers.get("cust_1?admin=1")
        sent = http.request_history[0]

    assert sent.path_url == "/v1/customers/cust_1%3Fadmin%3D1"
    assert sent.query == ""


def test_an_id_containing_a_fragment_marker_is_escaped():
    client = make_client()

    with requests_mock.Mocker() as http:
        http.get(requests_mock.ANY, json={"id": "sub_1"})

        client.subscriptions.get("sub_1#anchor")
        sent = http.request_history[0]

    assert sent.path_url == "/v1/subscriptions/sub_1%23anchor"


def test_ordinary_ids_are_unchanged_on_the_wire():
    # The escaping must be a provable no-op for the ids merchants actually use.
    client = make_client()

    with requests_mock.Mocker() as http:
        http.get(requests_mock.ANY, json={"id": "pay_01HZY3ABC"})

        client.payments.get("pay_01HZY3ABC")
        assert http.request_history[0].path_url == "/v1/payments/pay_01HZY3ABC"
