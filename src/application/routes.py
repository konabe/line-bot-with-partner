import json

from flask import abort, request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler

from ..infrastructure.logger import create_logger

logger = create_logger(__name__)


def register_routes(app, handler: WebhookHandler, line_adapter):
    @app.route("/health", methods=["GET"])
    def health():
        logger.debug("/health endpoint called")
        return "ok", 200

    @app.route("/callback", methods=["POST"])
    def callback():
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)
        logger.debug(f"/callback called. Signature: {signature}, Body: {body}")
        try:
            handler.handle(body, signature)
            logger.debug("handler.handle succeeded")
        except InvalidSignatureError:
            logger.error("InvalidSignatureError: signature invalid")
            _handle_signature_error(body, line_adapter)
            abort(400)
        except Exception as e:
            logger.error(f"Exception in handler.handle: {e}")
            _handle_general_error(body, line_adapter)
            abort(500)
        return "OK", 200


def _handle_signature_error(body, line_adapter):
    try:
        data = json.loads(body)
        for ev in data.get("events", []):
            reply_token = ev.get("replyToken")
            if reply_token:
                reply_message_request = ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(
                            text="署名検証に失敗しました。管理者に連絡してください。",
                            quickReply=None,
                            quoteToken=None,
                        )
                    ],
                    notificationDisabled=False,
                )
                line_adapter.reply_message(reply_message_request)
    except Exception as ex:
        logger.error(f"障害通知送信失敗: {ex}")


def _handle_general_error(body, line_adapter):
    try:
        data = json.loads(body)
        for ev in data.get("events", []):
            reply_token = ev.get("replyToken")
            if reply_token:
                reply_message_request = ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(
                            text="現在障害が発生しています。管理者に連絡してください。",
                            quickReply=None,
                            quoteToken=None,
                        )
                    ],
                    notificationDisabled=False,
                )
                line_adapter.reply_message(reply_message_request)
    except Exception as ex:
        logger.error(f"障害通知送信失敗: {ex}")
