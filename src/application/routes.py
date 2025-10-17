import logging
import json
from flask import request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

logger = logging.getLogger(__name__)


def register_routes(app, handler: WebhookHandler, safe_reply_message):
    @app.route('/health', methods=['GET'])
    def health():
        logger.debug("/health endpoint called")
        return 'ok', 200

    @app.route('/callback', methods=['POST'])
    def callback():
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        logger.debug(f"/callback called. Signature: {signature}, Body: {body}")
        try:
            handler.handle(body, signature)
            logger.debug("handler.handle succeeded")
        except InvalidSignatureError:
            logger.error("InvalidSignatureError: signature invalid")
            _handle_signature_error(body, safe_reply_message)
            abort(400)
        except Exception as e:
            logger.error(f"Exception in handler.handle: {e}")
            _handle_general_error(body, safe_reply_message)
            abort(500)
        return 'OK', 200


def _handle_signature_error(body, safe_reply_message):
    """InvalidSignatureError を処理し、ユーザーにエラーメッセージを送信します。"""
    try:
        data = json.loads(body)
        for ev in data.get('events', []):
            reply_token = ev.get('replyToken')
            if reply_token:
                reply_message_request = ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text='署名検証に失敗しました。管理者に連絡してください。')]
                )
                safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(ev))
    except Exception as ex:
        logger.error(f"障害通知送信失敗: {ex}")


def _handle_general_error(body, safe_reply_message):
    """一般的な例外を処理し、ユーザーにエラーメッセージを送信します。"""
    try:
        data = json.loads(body)
        for ev in data.get('events', []):
            reply_token = ev.get('replyToken')
            if reply_token:
                reply_message_request = ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text='現在障害が発生しています。管理者に連絡してください。')]
                )
                safe_reply_message(reply_message_request, fallback_to=get_fallback_destination(ev))
    except Exception as ex:
        logger.error(f"障害通知送信失敗: {ex}")


def get_fallback_destination(event):
    """プッシュフォールバック用の宛先 ID を返します。userId → groupId → roomId の優先順位で選択します。"""
    try:
        src = getattr(event, 'source', None)
        if not src:
            return None
        return (
            getattr(src, 'user_id', None)
            or getattr(src, 'userId', None)
            or getattr(src, 'group_id', None)
            or getattr(src, 'groupId', None)
            or getattr(src, 'room_id', None)
            or getattr(src, 'roomId', None)
        )
    except Exception:
        return None