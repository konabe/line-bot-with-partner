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

    # デフォルトの DomainServices をここで生成（遅延で OpenAIAdapter を生成）
    from ..domain import OpenAIAdapter
    from ..infrastructure.adapters.weather_adapter import WeatherAdapter

    _openai_holder: dict = {"client": None}
    _weather_adapter = WeatherAdapter()

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIAdapter()
        return _openai_holder["client"]

    class DefaultDomainServices:
        """DomainServicesプロトコルの実装"""

        def __init__(self):
            self.weather_adapter: object = _weather_adapter

        @property
        def openai_adapter(self):
            return _get_openai_client()

        def get_chatgpt_meal_suggestion(self) -> str:
            return _get_openai_client().get_chatgpt_meal_suggestion()

        def get_chatgpt_response(self, text: str) -> str:
            return _get_openai_client().get_chatgpt_response(text)

    default_domain_services = DefaultDomainServices()

    from ..infrastructure.adapters.line_adapter import LineMessagingAdapter

    # Create a Line adapter instance to be injected into handlers/usecases
    _line_adapter = LineMessagingAdapter(logger=create_logger(__name__))

    message_handler_instance = MessageHandler(
        safe_reply_message, default_domain_services, _line_adapter
    )

    def message_handler(event):
        return message_handler_instance.handle_message(event)

    # Instantiate PostbackHandler with injected logger and safe_reply_message
    # profile_getter is implemented in the infrastructure layer
    # Reuse the same LineMessagingAdapter for postback profile lookups
    _postback_handler_instance = PostbackHandler(
        create_logger(__name__),
        safe_reply_message,
        _line_adapter.get_display_name_from_line_profile,
    )

    def postback_handler(event):
        return _postback_handler_instance.handle_postback(event)

    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)
