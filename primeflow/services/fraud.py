from typing import Dict, Any

class FraudService:
    def __init__(self, client):
        self.client = client

    def get(self) -> Dict[str, Any]:
        return self.client.request("GET", "/v1/policies/fraud")

    def update(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/policies/fraud", json=policy)
