from typing import Any, Dict, List, Optional


def _extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload.get(key, [])
    return payload or []


class RoutingRulesService:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/routing-rules"), "rules")

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/routing-rules", json=data, headers=headers)

    def get(self, rule_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/routing-rules/{rule_id}")

    def update(self, rule_id: str, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("PATCH", f"/v1/routing-rules/{rule_id}", json=data, headers=headers)

    def delete(self, rule_id: str, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", f"/v1/routing-rules/{rule_id}", headers=headers)
