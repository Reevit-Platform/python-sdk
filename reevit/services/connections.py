from typing import List, Dict, Any, Optional

class ConnectionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/connections", json=data, headers=headers)

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        response = self.client.request("GET", "/v1/connections", params=params)
        if isinstance(response, dict):
            return response.get("connections", [])
        return response

    def get(self, connection_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/connections/{connection_id}")

    def delete(self, connection_id: str, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", f"/v1/connections/{connection_id}", headers=headers)

    def validate(self, connection_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/connections/{connection_id}/validate", headers=headers)

    def list_audit(self, connection_id: str, **params: Any) -> List[Dict[str, Any]]:
        response = self.client.request("GET", f"/v1/connections/{connection_id}/audit", params=params)
        if isinstance(response, dict):
            return response.get("audit", [])
        return response

    def update_labels(self, connection_id: str, labels: List[str], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request(
            "PATCH",
            f"/v1/connections/{connection_id}/labels",
            json={"labels": labels},
            headers=headers,
        )

    def update_status(self, connection_id: str, status: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request(
            "PATCH",
            f"/v1/connections/{connection_id}/status",
            json={"status": status},
            headers=headers,
        )

    def test(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> bool:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        resp = self.client.request("POST", "/v1/connections/test", json=data, headers=headers)
        return resp.get("success", False)
