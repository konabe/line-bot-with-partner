import logging
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_event import PostbackEvent

logger = logging.getLogger(__name__)


def register_handlers(app, handler: WebhookHandler, safe_reply_message, safe_push_message):
    """Flask ルートと LINE webhook ハンドラーを指定された app/handler に登録します。

    この関数は、トップレベルの app モジュールからルーティングとイベント処理のロジックを
    分離するため、アプリケーション層の責任を明確にします。
    """
    # ハンドラーをインポート
    from .message_handlers import handle_message
    from .postback_handlers import handle_postback
    from .routes import register_routes, get_fallback_destination

    # ルートを登録
    register_routes(app, handler, safe_reply_message, safe_push_message)

    # 共通パラメータを持つ部分関数を作成
    def message_handler(event):
        return handle_message(event, safe_reply_message, get_fallback_destination)

    def postback_handler(event):
        return handle_postback(event, safe_reply_message, get_fallback_destination)

    # イベントハンドラーをアタッチ
    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)
