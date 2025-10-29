import logging

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.postback_event import PostbackEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent

from ..infrastructure.logger import create_logger
from .message_handlers import MessageHandler
from .postback_handlers import PostbackHandler
from .routes import register_routes

logger = logging.getLogger(__name__)


def register_handlers(app, handler: WebhookHandler, safe_reply_message):
    # ルートを登録
    register_routes(app, handler, safe_reply_message)

    # Create infrastructure adapters and a lazy OpenAI client holder.
    from ..domain import OpenAIAdapter
    from ..infrastructure.adapters.line_adapter import LineMessagingAdapter
    from ..infrastructure.adapters.weather_adapter import WeatherAdapter

    _openai_holder: dict = {"client": None}
    _weather_adapter = WeatherAdapter()

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIAdapter()
        return _openai_holder["client"]

    # Create a Line adapter instance to be injected into handlers/usecases
    _line_adapter = LineMessagingAdapter(logger=create_logger(__name__))

    message_handler_instance = MessageHandler(
        _line_adapter, _get_openai_client(), _weather_adapter
    )

    def message_handler(event):
        return message_handler_instance.handle_message(event)

    # Instantiate PostbackHandler with injected logger and safe_reply_message
    # profile_getter is implemented in the infrastructure layer
    # Reuse the same LineMessagingAdapter for postback profile lookups
    _postback_handler_instance = PostbackHandler(
        create_logger(__name__),
        _line_adapter,
    )

    def postback_handler(event):
        return _postback_handler_instance.handle_postback(event)

    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)
