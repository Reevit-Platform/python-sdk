from typing import List, Dict, Any

class SubscriptionsService:
    def __init__(self, client):
        self.client = client

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/subscriptions", json=data)

    def list(self) -> List[Dict[str, Any]]:
        return self.client.request("GET", "/v1/subscriptions")
