from typing import List, Dict, Any, Optional
from urllib.parse import quote

from reevit.services._list import extract_list as _extract_list


class ConnectionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", "/v1/connections", json=data, headers=headers)

    def list(self, **params: Any) -> List[Dict[str, Any]]:
        return self.list_page(**params)["connections"]

    def list_page(self, **params: Any) -> Dict[str, Any]:
        response = self.client.request("GET", "/v1/connections", params=params)
        if isinstance(response, list):
            return {
                "connections": response,
                "pagination": {
                    "total": len(response),
                    "limit": params.get("limit", len(response)),
                    "offset": params.get("offset", 0),
                },
            }
        if isinstance(response, dict):
            connections = _extract_list(response, "connections")
            data = response.get("data")
            has_shape = (
                isinstance(response.get("connections"), list)
                or isinstance(data, list)
                or (isinstance(data, dict) and isinstance(data.get("connections"), list))
            )
            if not has_shape:
                raise ValueError("unexpected connections response: missing connections array")
            pagination = response.get("pagination")
            if not isinstance(pagination, dict):
                pagination = {}
            return {
                "connections": connections,
                "pagination": {
                    "total": pagination.get("total", len(connections)),
                    "limit": pagination.get("limit", params.get("limit", len(connections))),
                    "offset": pagination.get("offset", params.get("offset", 0)),
                },
            }
        raise ValueError("unexpected connections response: expected an object")

    def list_all(
        self,
        *,
        label: Optional[str] = None,
        provider: Optional[str] = None,
        mode: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filters = {
            key: value
            for key, value in {
                "label": label,
                "provider": provider,
                "mode": mode,
                "status": status,
            }.items()
            if value is not None
        }
        connections = []
        offset = 0
        while True:
            page = self.list_page(**filters, limit=200, offset=offset)
            batch = page["connections"]
            connections.extend(batch)
            next_offset = offset + len(batch)
            if not batch or next_offset >= page["pagination"]["total"]:
                return connections
            offset = next_offset

    def get(self, connection_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/connections/{quote(connection_id, safe='')}")

    def delete(self, connection_id: str, idempotency_key: Optional[str] = None) -> None:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        self.client.request("DELETE", f"/v1/connections/{quote(connection_id, safe='')}", headers=headers)

    def validate(self, connection_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request("POST", f"/v1/connections/{quote(connection_id, safe='')}/validate", headers=headers)

    def list_audit(self, connection_id: str, **params: Any) -> List[Dict[str, Any]]:
        response = self.client.request("GET", f"/v1/connections/{quote(connection_id, safe='')}/audit", params=params)
        return _extract_list(response, "audit")

    def list_labels(self) -> List[Dict[str, Any]]:
        response = self.client.request("GET", "/v1/connections/labels")
        if not isinstance(response, list):
            raise ValueError("unexpected connection labels response: expected an array")
        return response

    def update_labels(self, connection_id: str, labels: List[str], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request(
            "PATCH",
            f"/v1/connections/{quote(connection_id, safe='')}/labels",
            json={"labels": labels},
            headers=headers,
        )

    def update_status(self, connection_id: str, status: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.request(
            "PATCH",
            f"/v1/connections/{quote(connection_id, safe='')}/status",
            json={"status": status},
            headers=headers,
        )

    def test(self, data: Dict[str, Any], idempotency_key: Optional[str] = None) -> bool:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        resp = self.client.request("POST", "/v1/connections/test", json=data, headers=headers)
        return resp.get("ok", resp.get("success", False))
