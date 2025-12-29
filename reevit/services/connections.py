from typing import List, Dict, Any

class ConnectionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/connections", json=data)

    def list(self) -> List[Dict[str, Any]]:
        return self.client.request("GET", "/v1/connections")

    def test(self, data: Dict[str, Any]) -> bool:
        resp = self.client.request("POST", "/v1/connections/test", json=data)
        return resp.get("success", False)
