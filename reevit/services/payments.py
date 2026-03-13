from typing import List, Dict, Any, Optional

class PaymentsService:
    def __init__(self, client):
        self.client = client

    def create_intent(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/payments/intents", json=data, headers=headers)

    def list(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        return self.client.request("GET", "/v1/payments", params=params)

    def get(self, payment_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/payments/{payment_id}")

    def update_intent(self, payment_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/payments/intents/{payment_id}", json=data, headers=headers)

    def confirm(self, payment_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/payments/{payment_id}/confirm", json={}, headers=headers)

    def confirm_intent(self, payment_id: str, client_secret: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request(
            "POST",
            f"/v1/payments/{payment_id}/confirm-intent",
            params={"client_secret": client_secret},
            json={},
            headers=headers,
        )

    def cancel(self, payment_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/payments/{payment_id}/cancel", json={}, headers=headers)

    def retry(self, payment_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/payments/{payment_id}/retry", json={}, headers=headers)

    def refund(self, payment_id: str, amount: Optional[int] = None, reason: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        data = {}
        if amount is not None:
            data["amount"] = amount
        if reason is not None:
            data["reason"] = reason
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/payments/{payment_id}/refund", json=data, headers=headers)

    def stats(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "/v1/payments/stats", params=params)
