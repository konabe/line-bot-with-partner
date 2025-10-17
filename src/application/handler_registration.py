import logging
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_event import PostbackEvent
from .message_handlers import MessageHandler
from .postback_handlers import handle_postback
from .routes import register_routes, get_fallback_destination

logger = logging.getLogger(__name__)

def register_handlers(app, handler: WebhookHandler, safe_reply_message):
    # ルートを登録
    register_routes(app, handler, safe_reply_message)

    message_handler_instance = MessageHandler(safe_reply_message, get_fallback_destination)

    def message_handler(event):
        return message_handler_instance.handle_message(event)

    def postback_handler(event):
        return handle_postback(event, safe_reply_message, get_fallback_destination)

    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)
