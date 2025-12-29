from typing import List, Dict, Any, Optional

class PaymentsService:
    def __init__(self, client):
        self.client = client

    def create_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/payments/intents", json=data)

    def list(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        return self.client.request("GET", "/v1/payments", params=params)

    def get(self, payment_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/payments/{payment_id}")

    def refund(self, payment_id: str, amount: Optional[int] = None, reason: Optional[str] = None) -> Dict[str, Any]:
        data = {}
        if amount is not None:
            data["amount"] = amount
        if reason is not None:
            data["reason"] = reason
        return self.client.request("POST", f"/v1/payments/{payment_id}/refund", json=data)
