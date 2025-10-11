import pytest
from app import app

def test_health():
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.data == b'ok'

def test_callback_invalid_signature():
    with app.test_client() as client:
        # X-Line-Signatureが不正な場合は400
        response = client.post('/callback', headers={'X-Line-Signature': 'invalid'}, data='{}')
        assert response.status_code == 400

def test_callback_valid_signature():
    import hmac
    import hashlib
    import base64
    import os
    # LINE公式Webhook仕様に合わせたMessageEvent JSON
    import json
    body_dict = {
        "destination": "U123",
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "id": "1234567890", "text": "じゃんけん"},
                "timestamp": 1600000000000,
                "source": {"type": "user", "userId": "U123"},
                "replyToken": "dummy",
                "mode": "active",
                "webhookEventId": "testid",
                "deliveryContext": {"isRedelivery": False}
            }
        ]
    }
    body = json.dumps(body_dict, ensure_ascii=False, separators=(',', ':'))
    secret = os.environ.get('LINE_CHANNEL_SECRET', '')
    signature = base64.b64encode(hmac.new(secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    with app.test_client() as client:
        response = client.post(
            '/callback',
            headers={
                'X-Line-Signature': signature,
                'Content-Type': 'application/json'
            },
            data=body
        )
        assert response.status_code == 200
        assert response.data == b'OK'
