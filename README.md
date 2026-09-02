# Reevit Python SDK

The official Python SDK for [Reevit](https://reevit.io) — a unified payment orchestration platform for Africa.

[![PyPI version](https://img.shields.io/pypi/v/reevit.svg)](https://pypi.org/project/reevit/)
[![Python versions](https://img.shields.io/pypi/pyversions/reevit.svg)](https://pypi.org/project/reevit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install reevit
```

## Quick Start

```python
from reevit import Reevit

client = Reevit(api_key="pfk_live_xxx", org_id="org_123")

# Create a payment
try:
    payment = client.payments.create_intent({
        "amount": 5000,  # 50.00 GHS
        "currency": "GHS",
        "method": "momo",
        "country": "GH",
        "customer_id": "cust_123",
        "metadata": {
            "order_id": "12345"
        }
    }, idempotency_key="order_12345")
    print(f"Payment created: {payment['id']}")
except Exception as e:
    print(f"Error: {e}")

# List payments
payments = client.payments.list()
print(payments)
```

## Server-created checkout sessions

Create checkout sessions on your server, then pass `session["session_secret"]` to a browser SDK — [`@reevit/react`](https://www.npmjs.com/package/@reevit/react), [`@reevit/vue`](https://www.npmjs.com/package/@reevit/vue), or [`@reevit/svelte`](https://www.npmjs.com/package/@reevit/svelte) — to render the checkout UI.

```python
session = client.checkout_sessions.create(
    {
        "amount": 5000,
        "currency": "GHS",
        "method": "mobile_money",
        "country": "GH",
    },
    idempotency_key="order_12345",
)
```

## Idempotency

Pass `idempotency_key` to safely retry intent creation without duplicates.

```python
payment = client.payments.create_intent(
    {
        "amount": 5000,
        "currency": "GHS",
        "method": "momo",
        "country": "GH",
    },
    idempotency_key="order_12345",
)
```

## Error handling

Every failed API call raises `ReevitAPIError`.

```python
from reevit import Reevit, ReevitAPIError

try:
    payment = client.payments.get("pay_123")
except ReevitAPIError as error:
    print(error.status_code)  # HTTP status, or 0 for client-side errors
    print(error.code)         # machine-readable code, e.g. "not_found"
    print(error.details)      # dict of extra context, may be empty
    print(error.request_id)   # X-Request-Id of the failed response, or None
```

`request_id` is read from the response's `X-Request-Id` header (falling back to
`X-Reevit-Request-Id`) and is appended to `str(error)`, so it shows up in logs
without any extra work. Quote it when you open a support ticket — it is the
handle that ties your failure to a server-side log line.

### `unexpected_response_shape`

List helpers raise `ReevitAPIError(status_code=0, code="unexpected_response_shape")`
when a response body contains no list the SDK recognises. They deliberately do
**not** return `[]` in that case: an empty list is a real answer ("this merchant
has no payments"), and a reconciliation job must not silently report zero
settlements because a response shape changed. A recognised container that is
genuinely empty still returns `[]`.

## Features

- **Payments**: Create intents, update intents, confirm, confirm intent, cancel, retry, refund, stats
- **Connections**: Manage PSP integrations, validation, labels, status, audit
- **Subscriptions**: Manage recurring billing lifecycle
- **Fraud**: Configure fraud rules
- **Customers / Payment Links / Checkout Sessions / Webhooks / Routing Rules / Invoices**: Additional backend services

`org_id` is supported directly on the client. Omitting it for authenticated requests still works for backward compatibility, but that mode is deprecated.

To fetch every connected PSP rather than one page:

```python
connections = client.connections.list_all(mode="live", status="active")
page = client.connections.list_page(limit=50, offset=0)
```

---

## Webhook Verification

Reevit sends webhooks to notify your application of payment events. Always verify webhook signatures.

### Understanding Webhooks

There are **two types of webhooks** in Reevit:

1. **Inbound Webhooks (PSP → Reevit)**: Webhooks from payment providers (Paystack, Flutterwave, etc.) to Reevit. Configure these in the PSP dashboard. Reevit handles them automatically.

2. **Outbound Webhooks (Reevit → Your App)**: Webhooks from Reevit to your application. Configure in Reevit Dashboard and create a handler in your app.

### Signature Format

- **Header**: `X-Reevit-Signature: sha256=<hex-signature>`
- **Signature**: `HMAC-SHA256(request_body, signing_secret)`

### Verifying a delivery

`construct_event` is the one call a handler needs: it verifies the HMAC over the
raw bytes, rejects replays outside a 5-minute window, and only then parses the
body — so there is no way to act on an unverified payload.

```python
from reevit import construct_event, WebhookVerificationError

try:
    event = construct_event(raw_body, request.headers.get("X-Reevit-Signature"), SECRET)
except WebhookVerificationError as error:
    # error.code: invalid_signature | invalid_payload
    #             missing_signature_timestamp | timestamp_out_of_tolerance
    return "", 401

print(event["event"], event["data"])
```

Pass `tolerance_seconds=` to widen or narrow the replay window (default `300`,
checked in both directions so modest clock skew does not drop live deliveries).
`verify_webhook_signature_with_tolerance(...)` is the same check with a boolean
return, for handlers that parse the body themselves.

`verify_webhook_signature(...)` remains available and is unchanged: it checks
only the HMAC, so a delivery captured off the wire replays forever. Prefer
`construct_event`.

Verify against the exact bytes you received. Do not `json.loads` and
re-serialize the body first — key order and whitespace must match what Reevit
signed.

### Getting Your Signing Secret

1. Go to **Reevit Dashboard > Developers > Webhooks**
2. Configure your webhook endpoint URL
3. Copy the signing secret (starts with `whsec_`)
4. Set environment variable: `REEVIT_WEBHOOK_SECRET=whsec_xxx...`

### Flask Webhook Handler

The SDK ships a constant-time verifier — `verify_webhook_signature(payload, signature, secret)` — so you do not have to reimplement HMAC. Pass the **raw** request body (not parsed-and-reserialized JSON), the `X-Reevit-Signature` header, and your signing secret.

```python
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify
from reevit import verify_webhook_signature

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PaymentData:
    id: str
    status: str
    amount: int
    currency: str
    provider: str
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

@dataclass
class SubscriptionData:
    id: str
    customer_id: str
    plan_id: str
    status: str
    amount: int
    currency: str
    interval: str
    next_renewal_at: Optional[str] = None

@app.route('/webhooks/reevit', methods=['POST'])
def webhook():
    payload = request.get_data()  # raw bytes — do not re-serialize
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')

    # Verify signature (required in production)
    if not verify_webhook_signature(payload, signature, secret):
        logger.warning('[Webhook] Invalid signature')
        return jsonify({'error': 'Invalid signature'}), 401
    
    event = request.get_json()
    event_type = event.get('type')
    event_id = event.get('id')
    
    logger.info(f'[Webhook] Received: {event_type} ({event_id})')
    
    # Handle different event types
    if event_type == 'reevit.webhook.test':
        logger.info(f'[Webhook] Test received: {event.get("message")}')
    
    # Payment events
    elif event_type == 'payment.succeeded':
        data = PaymentData(**event.get('data', {}))
        handle_payment_succeeded(data)
    
    elif event_type == 'payment.failed':
        data = PaymentData(**event.get('data', {}))
        handle_payment_failed(data)
    
    elif event_type == 'payment.refunded':
        data = PaymentData(**event.get('data', {}))
        handle_payment_refunded(data)
    
    elif event_type == 'payment.pending':
        data = PaymentData(**event.get('data', {}))
        logger.info(f'[Webhook] Payment pending: {data.id}')
    
    # Subscription events
    elif event_type == 'subscription.created':
        data = SubscriptionData(**event.get('data', {}))
        handle_subscription_created(data)
    
    elif event_type == 'subscription.renewed':
        data = SubscriptionData(**event.get('data', {}))
        handle_subscription_renewed(data)
    
    elif event_type == 'subscription.canceled':
        data = SubscriptionData(**event.get('data', {}))
        handle_subscription_canceled(data)
    
    else:
        logger.info(f'[Webhook] Unhandled event: {event_type}')
    
    return jsonify({'received': True})

# Payment handlers
def handle_payment_succeeded(data: PaymentData):
    order_id = data.metadata.get('order_id') if data.metadata else None
    logger.info(f'[Webhook] Payment succeeded: {data.id} for order {order_id}')
    
    # TODO: Implement your business logic
    # - Update order status to "paid"
    # - Send confirmation email to customer
    # - Trigger fulfillment process

def handle_payment_failed(data: PaymentData):
    logger.info(f'[Webhook] Payment failed: {data.id}')
    
    # TODO: Implement your business logic
    # - Update order status to "payment_failed"
    # - Send notification to customer
    # - Allow retry

def handle_payment_refunded(data: PaymentData):
    order_id = data.metadata.get('order_id') if data.metadata else None
    logger.info(f'[Webhook] Payment refunded: {data.id} for order {order_id}')
    
    # TODO: Implement your business logic
    # - Update order status to "refunded"
    # - Restore inventory if applicable

# Subscription handlers
def handle_subscription_created(data: SubscriptionData):
    logger.info(f'[Webhook] Subscription created: {data.id} for customer {data.customer_id}')
    
    # TODO: Implement your business logic
    # - Grant access to subscription features
    # - Send welcome email

def handle_subscription_renewed(data: SubscriptionData):
    logger.info(f'[Webhook] Subscription renewed: {data.id}')
    
    # TODO: Implement your business logic
    # - Extend access period
    # - Send renewal confirmation

def handle_subscription_canceled(data: SubscriptionData):
    logger.info(f'[Webhook] Subscription canceled: {data.id}')
    
    # TODO: Implement your business logic
    # - Revoke access at end of billing period
    # - Send cancellation confirmation

if __name__ == '__main__':
    app.run(port=8080)
```

### Django Webhook Handler

```python
# views.py
import json
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from reevit import verify_webhook_signature

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def reevit_webhook(request):
    payload = request.body  # raw bytes — do not re-serialize
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')
    
    if not verify_webhook_signature(payload, signature, secret):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    event = json.loads(payload)
    event_type = event.get('type')
    
    logger.info(f'[Webhook] Received: {event_type}')
    
    if event_type == 'payment.succeeded':
        data = event.get('data', {})
        order_id = data.get('metadata', {}).get('order_id')
        # Fulfill order, send confirmation email
        logger.info(f'Payment succeeded for order {order_id}')
    
    elif event_type == 'payment.failed':
        # Notify customer, allow retry
        pass
    
    elif event_type == 'subscription.renewed':
        # Extend access
        pass
    
    elif event_type == 'subscription.canceled':
        # Revoke access
        pass
    
    return JsonResponse({'received': True})
```

### FastAPI Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import os
import logging
from reevit import verify_webhook_signature

app = FastAPI()
logger = logging.getLogger(__name__)

class PaymentData(BaseModel):
    id: str
    status: str
    amount: int
    currency: str
    provider: str
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

class SubscriptionData(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    status: str
    amount: int
    currency: str
    interval: str
    next_renewal_at: Optional[str] = None

@app.post('/webhooks/reevit')
async def webhook(request: Request):
    payload = await request.body()  # raw bytes — do not re-serialize
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')
    
    if not verify_webhook_signature(payload, signature, secret):
        raise HTTPException(status_code=401, detail='Invalid signature')
    
    event = await request.json()
    event_type = event.get('type')
    
    logger.info(f'[Webhook] Received: {event_type}')
    
    # Payment events
    if event_type == 'payment.succeeded':
        data = PaymentData(**event.get('data', {}))
        order_id = data.metadata.get('order_id') if data.metadata else None
        logger.info(f'Payment succeeded: {data.id} for order {order_id}')
        # Fulfill order, send confirmation email
    
    elif event_type == 'payment.failed':
        # Notify customer, allow retry
        pass
    
    # Subscription events
    elif event_type == 'subscription.renewed':
        data = SubscriptionData(**event.get('data', {}))
        logger.info(f'Subscription renewed: {data.id}')
        # Extend access
    
    elif event_type == 'subscription.canceled':
        data = SubscriptionData(**event.get('data', {}))
        logger.info(f'Subscription canceled: {data.id}')
        # Revoke access
    
    return {'received': True}
```

## Supported PSPs

| Provider | Countries | Payment Methods |
|----------|-----------|-----------------|
| Paystack | NG, GH, ZA, KE | Card, Mobile Money, Bank Transfer |
| Flutterwave | NG, GH, KE, ZA + | Card, Mobile Money, Bank Transfer |
| Hubtel | GH | Mobile Money |
| Stripe | Global (50+) | Card, Apple Pay, Google Pay |
| Monnify | NG | Card, Bank Transfer, USSD |
| M-Pesa | KE, TZ | Mobile Money (STK Push) |

---

## Release Notes

### v0.9.1

- Added `verify_webhook_signature` / `sign_webhook_payload` helpers (constant-time HMAC-SHA256 verification of the `X-Reevit-Signature` header)
- Version is now sourced from `reevit._version` and sent as the `X-Reevit-Client-Version` header

### v0.9.0

- Added server-created checkout sessions
- Version alignment across all Reevit SDKs
- Updated documentation and webhook examples
- Added support for Apple Pay and Google Pay
- Updated supported PSPs and payment methods documentation

---

## Environment Variables

```bash
export REEVIT_API_KEY=pfk_live_xxx
export REEVIT_ORG_ID=org_xxx
export REEVIT_WEBHOOK_SECRET=whsec_xxx  # Get from Dashboard > Developers > Webhooks
```

---

## Support

- **Documentation**: [https://docs.reevit.io](https://docs.reevit.io)
- **GitHub Issues**: [https://github.com/Reevit-Platform/backend/issues](https://github.com/Reevit-Platform/backend/issues)
- **Email**: support@reevit.io

## License

MIT License - see [LICENSE](LICENSE) for details.
