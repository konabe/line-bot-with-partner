import pytest
from src.app import app

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


def test_callback_pokemon_flow():
    # Instead of exercising the webhook stack (which depends on WebhookHandler
    # and signature handling), call MessageHandler.handle_message directly with
    # a fake event and ensure the mock adapter receives a reply. This keeps the
    # test deterministic and focuses on the "ポケモン" flow.
    from src.infrastructure import register_adapter
    from tests.support.mock_adapter import MockMessagingAdapter
    from src.application.message_handlers import MessageHandler
    from types import SimpleNamespace
    from src.domain import OpenAIClient

    # register mock adapter
    mock = MockMessagingAdapter()
    register_adapter(mock)
    mock.init('test-token')

    # create a minimal default_domain_services similar to handler_registration
    _openai_holder = {"client": None}

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIClient()
        return _openai_holder["client"]

    default_domain_services = SimpleNamespace(
        get_chatgpt_meal_suggestion=lambda: _get_openai_client().get_chatgpt_meal_suggestion(),
        get_chatgpt_response=lambda text: _get_openai_client().get_chatgpt_response(text),
        get_weather_text=lambda location: '東京: 晴れ',
        weather_adapter=SimpleNamespace(get_weather_text=lambda location: '東京: 晴れ'),
    )

    handler = MessageHandler(mock.reply_message, default_domain_services)

    # build a fake event object expected by MessageHandler
    class FakeMessage:
        def __init__(self, text):
            self.text = text

    class FakeSource:
        def __init__(self, userId):
            self.userId = userId

    class FakeEvent:
        def __init__(self, text, userId='U123'):
            self.message = FakeMessage(text)
            self.source = FakeSource(userId)
            self.reply_token = 'dummy'

    event = FakeEvent('ポケモン')

    # Call handler
    handler.handle_message(event)

    # ensure a reply was sent through the mock adapter
    replies = mock.get_replies()
    assert len(replies) >= 1
