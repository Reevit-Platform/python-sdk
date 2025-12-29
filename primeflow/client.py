import requests
from typing import Optional, Dict, Any
from .services.payments import PaymentsService
from .services.connections import ConnectionsService
from .services.subscriptions import SubscriptionsService
from .services.fraud import FraudService

API_BASE_URL_PRODUCTION = 'https://api.reevit.io'
API_BASE_URL_SANDBOX = 'https://sandbox-api.reevit.io'
DEFAULT_TIMEOUT = 30

def is_sandbox_key(api_key: str) -> bool:
    return api_key.startswith('pk_test_') or api_key.startswith('pk_sandbox_')

class Reevit:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        if base_url is None:
            base_url = API_BASE_URL_SANDBOX if is_sandbox_key(api_key) else API_BASE_URL_PRODUCTION
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "@reevit/python",
            "Authorization": f"Bearer {api_key}",
            "X-Reevit-Client": "@reevit/python",
            "X-Reevit-Client-Version": "0.3.2",
        })
        self.base_url = base_url.rstrip("/")

        self.payments = PaymentsService(self)
        self.connections = ConnectionsService(self)
        self.subscriptions = SubscriptionsService(self)
        self.fraud = FraudService(self)

    def request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        if 'timeout' not in kwargs:
            kwargs['timeout'] = DEFAULT_TIMEOUT
        response = self.session.request(method, url, **kwargs)
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Attempt to return the error body if JSON
            try:
                return response.json()
            except:
                raise e
