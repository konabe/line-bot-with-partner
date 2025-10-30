import logging

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.postback_event import PostbackEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent

from ..infrastructure.logger import create_logger
from .message_router import MessageRouter
from .postback_router import PostbackRouter
from .register_flask_routes import register_routes
from .usecases.send_startup_notification_usecase import SendStartupNotificationUsecase

logger = logging.getLogger(__name__)


def register_handlers(
    app, handler: WebhookHandler, safe_reply_message, line_adapter=None
):
    from ..infrastructure.adapters.line_adapter import LineMessagingAdapter

    _line_adapter = line_adapter or LineMessagingAdapter(logger=create_logger(__name__))

    register_routes(app, handler, _line_adapter)

    from ..domain import OpenAIAdapter
    from ..infrastructure.adapters.pokemon_adapter import PokemonApiAdapter
    from ..infrastructure.adapters.weather_adapter import WeatherAdapter

    _openai_holder: dict = {"client": None}
    _weather_adapter = WeatherAdapter()
    _pokemon_adapter = PokemonApiAdapter()

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIAdapter()
        return _openai_holder["client"]

    message_router_instance = MessageRouter(
        _line_adapter,
        _get_openai_client(),
        _weather_adapter,
        _pokemon_adapter,
        logger=create_logger(__name__),
    )

    def message_handler(event):
        return message_router_instance.route_message(event)

    postback_router_instance = PostbackRouter(
        _line_adapter,
        logger=create_logger(__name__),
        janken_service=message_router_instance.janken_service,
    )

    def postback_handler(event):
        return postback_router_instance.route_postback(event)

    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)


def create_startup_notification_usecase(line_adapter) -> SendStartupNotificationUsecase:
    return SendStartupNotificationUsecase(line_adapter, create_logger(__name__))
