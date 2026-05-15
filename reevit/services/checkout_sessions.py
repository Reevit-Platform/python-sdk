from typing import Dict, Any, Optional


class CheckoutSessionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/checkout/sessions", json=data, headers=headers)
