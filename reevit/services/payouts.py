from typing import Any, Dict, Optional
from reevit.services._paths import seg as _seg


class PayoutsService:
    def __init__(self, client):
        self.client = client

    def create(
        self,
        data: Dict[str, Any],
        *,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        self._require_idempotency_key(idempotency_key)
        return self.client.request(
            "POST",
            "/v1/payouts",
            json=data,
            headers={"Idempotency-Key": idempotency_key},
        )

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self.client.request("GET", "/v1/payouts", params=params)

    def get(self, payout_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/payouts/{_seg(payout_id)}")

    def confirm(self, payout_id: str) -> Dict[str, Any]:
        return self.client.request("POST", f"/v1/payouts/{_seg(payout_id)}/confirm", json={})

    def cancel(self, payout_id: str) -> Dict[str, Any]:
        return self.client.request("POST", f"/v1/payouts/{_seg(payout_id)}/cancel", json={})

    def create_bulk(
        self,
        data: Dict[str, Any],
        *,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        self._require_idempotency_key(idempotency_key)
        return self.client.request(
            "POST",
            "/v1/payouts/bulk",
            json=data,
            headers={"Idempotency-Key": idempotency_key},
        )

    def balance(self, connection_id: str) -> Dict[str, Any]:
        return self.client.request(
            "GET",
            "/v1/payouts/balance",
            params={"connection_id": connection_id},
        )

    def resolve_account(
        self,
        connection_id: str,
        beneficiary: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.client.request(
            "POST",
            "/v1/payouts/resolve-account",
            json={"connection_id": connection_id, "beneficiary": beneficiary},
        )

    def create_beneficiary(self, beneficiary: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request(
            "POST",
            "/v1/beneficiaries",
            json={"beneficiary": beneficiary},
        )

    def list_beneficiaries(self, *, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        return self.client.request(
            "GET",
            "/v1/beneficiaries",
            params={"limit": limit, "offset": offset},
        )

    def get_beneficiary(self, beneficiary_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/beneficiaries/{_seg(beneficiary_id)}")

    def delete_beneficiary(self, beneficiary_id: str) -> Dict[str, Any]:
        return self.client.request("DELETE", f"/v1/beneficiaries/{_seg(beneficiary_id)}")

    @staticmethod
    def _require_idempotency_key(idempotency_key: str) -> None:
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("idempotency_key is required for payout creation")
