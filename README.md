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

client = Reevit(api_key="pfk_live_xxx")

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
    })
    print(f"Payment created: {payment['id']}")
except Exception as e:
    print(f"Error: {e}")

# List payments
payments = client.payments.list()
print(payments)
```

## Features

- **Payments**: Create intents, refund, list
- **Connections**: Manage PSP integrations
- **Subscriptions**: Manage recurring billing
- **Fraud**: Configure fraud rules

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

### Getting Your Signing Secret

1. Go to **Reevit Dashboard > Developers > Webhooks**
2. Configure your webhook endpoint URL
3. Copy the signing secret (starts with `whsec_`)
4. Set environment variable: `REEVIT_WEBHOOK_SECRET=whsec_xxx...`

### Flask Webhook Handler

```python
import hmac
import hashlib
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify

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

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature using HMAC-SHA256."""
    if not signature.startswith('sha256='):
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received = signature[7:]  # Remove "sha256=" prefix
    return hmac.compare_digest(received, expected)

@app.route('/webhooks/reevit', methods=['POST'])
def webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')
    
    # Verify signature (required in production)
    if secret and not verify_signature(payload, signature, secret):
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
import hmac
import hashlib
import json
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature.startswith('sha256='):
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received = signature[7:]
    return hmac.compare_digest(received, expected)

@csrf_exempt
@require_POST
def reevit_webhook(request):
    payload = request.body
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')
    
    if secret and not verify_signature(payload, signature, secret):
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
import hmac
import hashlib
import os
import logging

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

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature.startswith('sha256='):
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received = signature[7:]
    return hmac.compare_digest(received, expected)

@app.post('/webhooks/reevit')
async def webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Reevit-Signature', '')
    secret = os.environ.get('REEVIT_WEBHOOK_SECRET', '')
    
    if secret and not verify_signature(payload, signature, secret):
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
