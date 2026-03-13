from typing import Any, Dict, List, Optional


def _extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload.get(key, [])
    return payload or []


class PaymentLinksService:
    def __init__(self, client):
        self.client = client

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/payment-links", params=params), "payment_links")

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/payment-links", json=data, headers=headers)

    def get(self, payment_link_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/payment-links/{payment_link_id}")

    def update(self, payment_link_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/payment-links/{payment_link_id}", json=data, headers=headers)

    def delete(self, payment_link_id: str, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", f"/v1/payment-links/{payment_link_id}", headers=headers)

    def get_stats(self, payment_link_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/payment-links/{payment_link_id}/stats")

    def list_payments(self, payment_link_id: str, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(
            self.client.request("GET", f"/v1/payment-links/{payment_link_id}/payments", params=params),
            "payments",
        )

    def get_by_code(self, code: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/pay/{code}")
