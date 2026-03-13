from typing import Any, Dict, List, Optional


def _extract_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload.get(key, [])
    return payload or []


class WebhooksService:
    def __init__(self, client):
        self.client = client

    def get_config(self) -> Dict[str, Any]:
        return self.client.request("GET", "/v1/webhooks/config")

    def upsert_config(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/webhooks/config", json=data, headers=headers)

    def delete_config(self, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", "/v1/webhooks/config", headers=headers)

    def send_test(self, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/webhooks/test", json={}, headers=headers)

    def list_events(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/webhooks/events", params=params), "events")

    def get_event(self, event_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/webhooks/events/{event_id}")

    def replay_event(self, event_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/webhooks/events/{event_id}/replay", json={}, headers=headers)

    def list_outbound(self, **params: Any) -> List[Dict[str, Any]]:
        return _extract_list(self.client.request("GET", "/v1/webhooks/outbound", params=params), "outbound")

    def get_outbound(self, outbound_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/webhooks/outbound/{outbound_id}")
