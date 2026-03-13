from typing import Any, Dict, List, Optional


def _extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload.get(key, [])
    return payload or []


class CustomersService:
    def __init__(self, client):
        self.client = client

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/customers", params=params), "customers")

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/customers", json=data, headers=headers)

    def get(self, customer_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/customers/{customer_id}")

    def update(self, customer_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/customers/{customer_id}", json=data, headers=headers)

    def delete(self, customer_id: str, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", f"/v1/customers/{customer_id}", headers=headers)

    def lookup(self, external_id: str) -> Dict[str, Any]:
        return self.client.request("GET", "/v1/customers/lookup", params={"external_id": external_id})

    def top(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/customers/top", params=params), "customers")

    def payment_history(self, customer_id: str, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", f"/v1/customers/{customer_id}/payments", params=params), "payments")
