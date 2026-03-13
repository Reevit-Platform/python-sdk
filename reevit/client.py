import requests
import warnings
from typing import Optional, Dict, Any
from .services.payments import PaymentsService
from .services.connections import ConnectionsService
from .services.subscriptions import SubscriptionsService
from .services.fraud import FraudService
from .services.customers import CustomersService
from .services.payment_links import PaymentLinksService
from .services.webhooks import WebhooksService
from .services.routing_rules import RoutingRulesService
from .services.invoices import InvoicesService

API_BASE_URL_PRODUCTION = 'https://api.reevit.io'
DEFAULT_TIMEOUT = 30

class ReevitAPIError(Exception):
    def __init__(self, status_code: int, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code or "api_error"
        self.details = details or {}
        super().__init__(message)

def is_sandbox_key(api_key: str) -> bool:
    return api_key.startswith('pfk_test_')

class Reevit:
    def __init__(self, api_key: str, org_id: Optional[str] = None, base_url: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        if base_url is None:
            base_url = API_BASE_URL_PRODUCTION
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "@reevit/python",
            "X-Reevit-Key": api_key,
            "X-Reevit-Client": "@reevit/python",
            "X-Reevit-Client-Version": "0.7.1",
        })
        if org_id:
            self.session.headers["X-Org-Id"] = org_id
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.timeout = timeout

        self.payments = PaymentsService(self)
        self.connections = ConnectionsService(self)
        self.subscriptions = SubscriptionsService(self)
        self.fraud = FraudService(self)
        self.customers = CustomersService(self)
        self.payment_links = PaymentLinksService(self)
        self.webhooks = WebhooksService(self)
        self.routing_rules = RoutingRulesService(self)
        self.invoices = InvoicesService(self)

    def request(self, method: str, path: str, **kwargs) -> Any:
        if not path.startswith("/v1/pay/") and not self.org_id:
            warnings.warn(
                "org_id should be provided for authenticated Reevit API requests; org-less usage is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
        url = f"{self.base_url}{path}"
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        headers = kwargs.pop('headers', None)
        if headers:
            merged_headers = dict(self.session.headers)
            merged_headers.update(headers)
            kwargs['headers'] = merged_headers
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 204:
            return None

        if not response.ok:
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            raise ReevitAPIError(
                response.status_code,
                payload.get("message") or response.text or "request failed",
                payload.get("code"),
                payload.get("details"),
            )

        try:
            return response.json()
        except ValueError:
            return None
