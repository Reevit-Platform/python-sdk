from typing import List, Dict, Any, Optional

class SubscriptionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/subscriptions", json=data, headers=headers)

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        return self.client.request("GET", "/v1/subscriptions", params=params)

    def get(self, subscription_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/subscriptions/{subscription_id}")

    def update(self, subscription_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/subscriptions/{subscription_id}", json=data, headers=headers)

    def cancel(self, subscription_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/subscriptions/{subscription_id}/cancel", json={}, headers=headers)

    def resume(self, subscription_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/subscriptions/{subscription_id}/resume", json={}, headers=headers)
