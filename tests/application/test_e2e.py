import os

# E2Eテスト用に必要な環境変数を事前に設定
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["LINE_CHANNEL_SECRET"] = "test-line-secret"
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test-line-token"

from src.app import app  # noqa: E402


def test_health():
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.data == b"ok"


def test_callback_invalid_signature():
    with app.test_client() as client:
        # X-Line-Signatureが不正な場合は400
        response = client.post(
            "/callback", headers={"X-Line-Signature": "invalid"}, data="{}"
        )
        assert response.status_code == 400


def test_callback_valid_signature():
    import base64
    import hashlib
    import hmac

    # LINE公式Webhook仕様に合わせたMessageEvent JSON
    import json
    import os

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
                "deliveryContext": {"isRedelivery": False},
            }
        ],
    }
    body = json.dumps(body_dict, ensure_ascii=False, separators=(",", ":"))
    secret = os.environ.get("LINE_CHANNEL_SECRET", "")
    signature = base64.b64encode(
        hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    with app.test_client() as client:
        response = client.post(
            "/callback",
            headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
            data=body,
        )
        assert response.status_code == 200
        assert response.data == b"OK"
