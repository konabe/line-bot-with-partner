import json
import time
from collections import OrderedDict

from flask import abort, request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler

from ..infrastructure.logger import create_logger

logger = create_logger(__name__)

# webhookEventIdの重複チェック用キャッシュ (最大1000件、1時間保持)
_processed_events = OrderedDict()
_MAX_CACHE_SIZE = 1000
_CACHE_TTL = 3600  # 1時間


def _is_duplicate_event(body: str) -> bool:
    try:
        data = json.loads(body)
        current_time = time.time()

        # 古いエントリを削除
        expired_keys = [
            k for k, v in _processed_events.items() if current_time - v > _CACHE_TTL
        ]
        for k in expired_keys:
            del _processed_events[k]

        # 各イベントのwebhookEventIdをチェック
        for event in data.get("events", []):
            webhook_event_id = event.get("webhookEventId")
            if not webhook_event_id:
                continue

            # 既に処理済みなら重複
            if webhook_event_id in _processed_events:
                logger.warning(f"Duplicate webhookEventId detected: {webhook_event_id}")
                return True

            # 新規イベントとして記録
            _processed_events[webhook_event_id] = current_time

            # キャッシュサイズ制限
            if len(_processed_events) > _MAX_CACHE_SIZE:
                _processed_events.popitem(last=False)

        return False
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(
            f"Error parsing event for duplicate check ({type(e).__name__}): {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error checking duplicate event ({type(e).__name__}): {e}"
        )
        return False


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

        # webhookEventIdの重複チェック
        if _is_duplicate_event(body):
            logger.info("Duplicate webhook event detected, skipping processing")
            return "OK", 200

        try:
            handler.handle(body, signature)
            logger.debug("handler.handle succeeded")
        except InvalidSignatureError:
            logger.error("InvalidSignatureError: signature invalid")
            _handle_signature_error(body, line_adapter)
            abort(400)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(
                f"Data processing error in handler.handle ({type(e).__name__}): {e}"
            )
            _handle_general_error(body, line_adapter)
            abort(500)
        except Exception as e:
            logger.error(
                f"Unexpected error in handler.handle ({type(e).__name__}): {e}"
            )
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
