from typing import Any, Dict, List, Optional


def _extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload.get(key, [])
    return payload or []


class InvoicesService:
    def __init__(self, client):
        self.client = client

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/invoices", params=params), "invoices")

    def get(self, invoice_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/invoices/{invoice_id}")

    def update(self, invoice_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/invoices/{invoice_id}", json=data, headers=headers)

    def cancel(self, invoice_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/invoices/{invoice_id}/cancel", json={}, headers=headers)

    def retry(self, invoice_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/invoices/{invoice_id}/retry", json={}, headers=headers)
